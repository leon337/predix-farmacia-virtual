begin;

alter table public.pfv_products
  add column if not exists anvisa_process text,
  add column if not exists registration_holder text,
  add column if not exists holder_cnpj text,
  add column if not exists source_mirror_url text,
  add column if not exists identity_real boolean not null default false,
  add column if not exists operations_simulated boolean not null default true;

create or replace function public.pfv_replace_catalog_from_json(
  p_catalog jsonb,
  p_catalog_sha text
)
returns jsonb
language plpgsql
security definer
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_before jsonb;
  v_after jsonb;
  v_count integer;
  v_unique integer;
  v_invalid integer;
begin
  if jsonb_typeof(p_catalog) <> 'object' or jsonb_typeof(p_catalog->'products') <> 'array' then
    raise exception 'Catálogo inválido: objeto/products ausente';
  end if;
  if jsonb_array_length(p_catalog->'products') <> 500 then
    raise exception 'Catálogo inválido: esperado 500 produtos, recebido %', jsonb_array_length(p_catalog->'products');
  end if;
  if coalesce(p_catalog #>> '{meta,identityIsReal}','false') <> 'true'
     or coalesce(p_catalog #>> '{meta,operationsAreSimulated}','false') <> 'true'
     or coalesce(p_catalog #>> '{meta,pricesAreUnavailable}','false') <> 'true' then
    raise exception 'Catálogo inválido: metadados de identidade/operação/preço';
  end if;
  if coalesce(p_catalog #>> '{meta,mirrorSha256}','') <> 'd20df633de53a2c79a2efa03ebae61db72fcb7e27941f23993784f179130f173' then
    raise exception 'Catálogo inválido: hash do espelho divergente';
  end if;
  if p_catalog_sha <> '322a842080af74e1cafeea0a98f0ea71a930ac442eadb1d6d9911e15b9b7cf34' then
    raise exception 'Catálogo inválido: hash do artefato divergente';
  end if;

  create temporary table pfv_catalog_stage (
    id bigint primary key,
    sku text not null,
    name text not null,
    category text not null,
    manufacturer text not null,
    active_ingredient text,
    presentation text not null,
    price_cents integer,
    prescription_required boolean not null,
    anvisa_registration text not null,
    anvisa_process text,
    registration_holder text,
    holder_cnpj text,
    source_url text not null,
    source_mirror_url text,
    source_updated_at text,
    risk_class text not null
  ) on commit drop;

  insert into pfv_catalog_stage(
    id,sku,name,category,manufacturer,active_ingredient,presentation,price_cents,
    prescription_required,anvisa_registration,anvisa_process,registration_holder,
    holder_cnpj,source_url,source_mirror_url,source_updated_at,risk_class
  )
  select
    x.id,x.sku,x.name,x.category,x.manufacturer,x."activeIngredient",x.presentation,x."priceCents",
    x."prescriptionRequired",x."anvisaRegistration",x."anvisaProcess",x."registrationHolder",
    x."holderCnpj",x."sourceUrl",x."sourceMirrorUrl",x."sourceUpdatedAt",x."riskClass"
  from jsonb_to_recordset(p_catalog->'products') as x(
    id bigint,
    sku text,
    name text,
    category text,
    manufacturer text,
    "activeIngredient" text,
    presentation text,
    "priceCents" integer,
    "prescriptionRequired" boolean,
    "anvisaRegistration" text,
    "anvisaProcess" text,
    "registrationHolder" text,
    "holderCnpj" text,
    "sourceUrl" text,
    "sourceMirrorUrl" text,
    "sourceUpdatedAt" text,
    "riskClass" text
  );

  select count(*),count(distinct (anvisa_registration,name,manufacturer))
    into v_count,v_unique from pfv_catalog_stage;
  select count(*) into v_invalid
  from pfv_catalog_stage
  where trim(name)=''
     or trim(manufacturer)=''
     or trim(anvisa_registration)=''
     or active_ingredient is not null
     or price_cents is not null
     or prescription_required
     or risk_class not in ('I','II','1','2')
     or source_url <> 'https://dados.anvisa.gov.br/dados/TA_PRODUTO_SAUDE_SITE.csv';

  if v_count <> 500 or v_unique <> 500 or v_invalid <> 0 then
    raise exception 'Catálogo rejeitado: count %, unique %, invalid %',v_count,v_unique,v_invalid;
  end if;

  select jsonb_build_object(
    'products',(select count(*) from public.pfv_products),
    'inventory',(select count(*) from public.pfv_inventory),
    'productQueries',(select count(*) from public.pfv_product_queries),
    'reservationItems',(select count(*) from public.pfv_reservation_items),
    'reservations',(select count(*) from public.pfv_reservations),
    'customers',(select count(*) from public.pfv_customers)
  ) into v_before;

  delete from public.pfv_product_queries;
  delete from public.pfv_reservation_items;
  delete from public.pfv_reservations;
  delete from public.pfv_customers;
  delete from public.pfv_inventory;
  delete from public.pfv_products;

  insert into public.pfv_products(
    id,sku,name,category,manufacturer,active_ingredient,presentation,price_cents,
    prescription_required,is_demo,anvisa_registration,source_url,source_updated_at,
    risk_class,anvisa_process,registration_holder,holder_cnpj,source_mirror_url,
    identity_real,operations_simulated
  )
  select
    id,sku,name,category,manufacturer,active_ingredient,presentation,price_cents,
    prescription_required,true,anvisa_registration,source_url,source_updated_at,
    risk_class,anvisa_process,registration_holder,holder_cnpj,source_mirror_url,
    true,true
  from pfv_catalog_stage
  order by id;

  insert into public.pfv_inventory(product_id,total,reserved,minimum,updated_at)
  select id,
         case when id % 17 = 0 then 0 else 12 + ((id * 37) % 109)::integer end,
         0,
         3 + (id % 10)::integer,
         now()
  from pfv_catalog_stage
  order by id;

  perform setval(pg_get_serial_sequence('public.pfv_products','id'),500,true);

  select jsonb_build_object(
    'products',(select count(*) from public.pfv_products),
    'realIdentities',(select count(*) from public.pfv_products where identity_real and anvisa_registration is not null),
    'pricesMissing',(select count(*) from public.pfv_products where price_cents is null),
    'inventory',(select count(*) from public.pfv_inventory),
    'negativeAvailability',(select count(*) from public.pfv_inventory where total-reserved<0),
    'catalogSha',p_catalog_sha
  ) into v_after;

  if (v_after->>'products')::integer <> 500
     or (v_after->>'realIdentities')::integer <> 500
     or (v_after->>'pricesMissing')::integer <> 500
     or (v_after->>'inventory')::integer <> 500
     or (v_after->>'negativeAvailability')::integer <> 0 then
    raise exception 'Validação pós-carga falhou: %',v_after;
  end if;

  insert into public.pfv_audit(actor,action,resource,before_json,after_json)
  values ('manoel','REAL_CATALOG_REPLACED','pfv_products',v_before,v_after);

  return jsonb_build_object('status','ok','before',v_before,'after',v_after);
end;
$function$;

revoke all on function public.pfv_replace_catalog_from_json(jsonb,text) from public;
grant execute on function public.pfv_replace_catalog_from_json(jsonb,text) to service_role;

commit;
