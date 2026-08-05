begin;

alter table public.pfv_products
  alter column price_cents drop not null,
  add column if not exists anvisa_registration text,
  add column if not exists source_url text,
  add column if not exists source_updated_at text,
  add column if not exists country text,
  add column if not exists risk_class text;

alter table public.pfv_reservation_items
  alter column price_cents drop not null;

create unique index if not exists pfv_products_anvisa_identity_uidx
  on public.pfv_products (anvisa_registration, name, manufacturer)
  where anvisa_registration is not null;

create or replace function public.pfv_create_reservation(
  p_customer_name text,
  p_contact text,
  p_product_id bigint,
  p_quantity integer,
  p_idempotency_key text
)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_existing uuid;
  v_customer uuid;
  v_reservation uuid;
  v_price integer;
  v_available integer;
  v_name text;
  v_expires_at timestamptz;
begin
  if coalesce(trim(p_customer_name),'') = '' then raise exception 'Cliente é obrigatório'; end if;
  if p_quantity is null or p_quantity <= 0 then raise exception 'Quantidade inválida'; end if;
  if coalesce(trim(p_idempotency_key),'') = '' then raise exception 'Idempotency-Key é obrigatório'; end if;

  select id into v_existing from public.pfv_reservations where idempotency_key=p_idempotency_key;
  if v_existing is not null then
    return (
      select jsonb_build_object(
        'id',r.id,
        'status',r.status,
        'expiresAt',r.expires_at,
        'createdAt',r.created_at,
        'totalCents',(
          select case when count(*) filter (where ri.price_cents is null)>0 then null
                      else sum(ri.price_cents*ri.quantity)::integer end
          from public.pfv_reservation_items ri where ri.reservation_id=r.id
        ),
        'isDemo',true
      )
      from public.pfv_reservations r where r.id=v_existing
    );
  end if;

  select p.name,p.price_cents,(i.total-i.reserved)
    into v_name,v_price,v_available
  from public.pfv_products p
  join public.pfv_inventory i on i.product_id=p.id
  where p.id=p_product_id
  for update of i;

  if v_name is null then raise exception 'Produto não encontrado'; end if;
  if p_quantity > v_available then raise exception 'Estoque insuficiente para %', v_name; end if;

  v_expires_at := now()+interval '60 minutes';
  insert into public.pfv_customers(name,contact)
    values (trim(p_customer_name),nullif(trim(p_contact),''))
    returning id into v_customer;
  insert into public.pfv_reservations(customer_id,status,expires_at,idempotency_key)
    values (v_customer,'ACTIVE',v_expires_at,p_idempotency_key)
    returning id into v_reservation;
  insert into public.pfv_reservation_items(reservation_id,product_id,quantity,price_cents)
    values (v_reservation,p_product_id,p_quantity,v_price);
  update public.pfv_inventory
    set reserved=reserved+p_quantity,updated_at=now()
    where product_id=p_product_id;
  insert into public.pfv_audit(actor,action,resource,after_json)
    values (
      'virtual-employee','RESERVATION_CREATED',v_reservation::text,
      jsonb_build_object('productId',p_product_id,'quantity',p_quantity,'priceAvailable',v_price is not null)
    );

  return jsonb_build_object(
    'id',v_reservation,
    'status','ACTIVE',
    'expiresAt',v_expires_at,
    'items',jsonb_build_array(jsonb_build_object(
      'productId',p_product_id,'name',v_name,'quantity',p_quantity,'priceCents',v_price
    )),
    'totalCents',case when v_price is null then null else v_price*p_quantity end,
    'isDemo',true
  );
end;
$function$;

revoke all on function public.pfv_create_reservation(text,text,bigint,integer,text) from public;
grant execute on function public.pfv_create_reservation(text,text,bigint,integer,text) to service_role;

insert into public.pfv_audit(actor,action,resource,after_json)
values ('manoel','CATALOG_SCHEMA_PREPARED','pfv_products',jsonb_build_object(
  'priceNullable',true,
  'anvisaMetadata',true,
  'reservationNullablePrice',true
));

commit;
