begin;

alter table public.pfv_products
  add column if not exists barcode text,
  add column if not exists image_url text,
  add column if not exists image_source text,
  add column if not exists image_verified_at timestamptz,
  add column if not exists source_dataset text;

create unique index if not exists pfv_products_barcode_key
  on public.pfv_products(barcode)
  where barcode is not null;

create or replace function public.pfv_replace_retail_catalog_from_json(
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
  v_unique_barcodes integer;
  v_unique_identities integer;
  v_invalid integer;
begin
  if jsonb_typeof(p_catalog) <> 'object' or jsonb_typeof(p_catalog->'products') <> 'array' then
    raise exception 'Catálogo inválido: objeto/products ausente';
  end if;
  if jsonb_array_length(p_catalog->'products') <> 500 then
    raise exception 'Catálogo inválido: esperado 500 produtos, recebido %', jsonb_array_length(p_catalog->'products');
  end if;
  if coalesce(p_catalog #>> '{meta,acceptedProducts}','0') <> '500'
     or coalesce(p_catalog #>> '{meta,distinctProducts}','0') <> '500'
     or coalesce(p_catalog #>> '{meta,productsWithImages}','0') <> '500'
     or coalesce(p_catalog #>> '{meta,stockUnitsAreSeparate}','false') <> 'true'
     or coalesce(p_catalog #>> '{meta,operationsAreSimulated}','false') <> 'true'
     or coalesce(p_catalog #>> '{meta,pricesAreUnavailable}','false') <> 'true' then
    raise exception 'Catálogo inválido: metadados de quantidade/imagem/operação/preço';
  end if;
  if trim(coalesce(p_catalog_sha,'')) = '' then
    raise exception 'Catálogo inválido: SHA-256 ausente';
  end if;

  create temporary table pfv_retail_catalog_stage (
    id bigint primary key,
    sku text not null,
    barcode text not null,
    name text not null,
    category text not null,
    manufacturer text not null,
    presentation text not null,
    price_cents integer,
    prescription_required boolean not null,
    identity_real boolean not null,
    operations_simulated boolean not null,
    image_url text not null,
    image_source text not null,
    image_verified_at timestamptz not null,
    source_url text not null,
    source_dataset text not null
  ) on commit drop;

  insert into pfv_retail_catalog_stage(
    id,sku,barcode,name,category,manufacturer,presentation,price_cents,
    prescription_required,identity_real,operations_simulated,image_url,
    image_source,image_verified_at,source_url,source_dataset
  )
  select
    x.id,x.sku,x.barcode,x.name,x.category,x.manufacturer,x.presentation,x."priceCents",
    x."prescriptionRequired",x."identityReal",x."operationsSimulated",x."imageUrl",
    x."imageSource",x."imageVerifiedAt"::timestamptz,x."sourceUrl",x."sourceDataset"
  from jsonb_to_recordset(p_catalog->'products') as x(
    id bigint,
    sku text,
    barcode text,
    name text,
    category text,
    manufacturer text,
    presentation text,
    "priceCents" integer,
    "prescriptionRequired" boolean,
    "identityReal" boolean,
    "operationsSimulated" boolean,
    "imageUrl" text,
    "imageSource" text,
    "imageVerifiedAt" text,
    "sourceUrl" text,
    "sourceDataset" text
  );

  select count(*), count(distinct barcode), count(distinct (lower(name),lower(manufacturer)))
    into v_count,v_unique_barcodes,v_unique_identities
  from pfv_retail_catalog_stage;

  select count(*) into v_invalid
  from pfv_retail_catalog_stage
  where trim(name)=''
     or trim(manufacturer)=''
     or trim(category)=''
     or barcode !~ '^[0-9]{8,14}$'
     or image_url !~ '^https://'
     or source_url !~ '^https://'
     or image_source not in ('Open Beauty Facts','Open Products Facts')
     or source_dataset not in ('Open Beauty Facts','Open Products Facts')
     or price_cents is not null
     or prescription_required
     or not identity_real
     or not operations_simulated;

  if v_count <> 500 or v_unique_barcodes <> 500 or v_unique_identities <> 500 or v_invalid <> 0 then
    raise exception 'Catálogo rejeitado: count %, barcodes %, identities %, invalid %',
      v_count,v_unique_barcodes,v_unique_identities,v_invalid;
  end if;

  select jsonb_build_object(
    'productRecords',(select count(*) from public.pfv_products),
    'inventoryRows',(select count(*) from public.pfv_inventory),
    'stockUnits',(select coalesce(sum(total),0) from public.pfv_inventory),
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
    id,sku,barcode,name,category,manufacturer,active_ingredient,presentation,
    price_cents,prescription_required,is_demo,anvisa_registration,source_url,
    source_updated_at,risk_class,anvisa_process,registration_holder,holder_cnpj,
    source_mirror_url,identity_real,operations_simulated,image_url,image_source,
    image_verified_at,source_dataset
  )
  select
    id,sku,barcode,name,category,manufacturer,null,presentation,
    null,false,true,null,source_url,null,null,null,null,null,
    null,true,true,image_url,image_source,image_verified_at,source_dataset
  from pfv_retail_catalog_stage
  order by id;

  insert into public.pfv_inventory(product_id,total,reserved,minimum,updated_at)
  select id,
         8 + ((id * 29) % 93)::integer,
         0,
         3 + (id % 8)::integer,
         now()
  from pfv_retail_catalog_stage
  order by id;

  perform setval(pg_get_serial_sequence('public.pfv_products','id'),500,true);

  select jsonb_build_object(
    'productRecords',(select count(*) from public.pfv_products),
    'distinctBarcodes',(select count(distinct barcode) from public.pfv_products),
    'productsWithImages',(select count(*) from public.pfv_products where image_url is not null),
    'inventoryRows',(select count(*) from public.pfv_inventory),
    'stockUnits',(select coalesce(sum(total),0) from public.pfv_inventory),
    'negativeAvailability',(select count(*) from public.pfv_inventory where total-reserved<0),
    'catalogSha',p_catalog_sha
  ) into v_after;

  if (v_after->>'productRecords')::integer <> 500
     or (v_after->>'distinctBarcodes')::integer <> 500
     or (v_after->>'productsWithImages')::integer <> 500
     or (v_after->>'inventoryRows')::integer <> 500
     or (v_after->>'negativeAvailability')::integer <> 0 then
    raise exception 'Validação pós-carga falhou: %',v_after;
  end if;

  insert into public.pfv_audit(actor,action,resource,before_json,after_json)
  values ('manoel','RETAIL_CATALOG_WITH_IMAGES_REPLACED','pfv_products',v_before,v_after);

  return jsonb_build_object('status','ok','before',v_before,'after',v_after);
end;
$function$;

revoke all on function public.pfv_replace_retail_catalog_from_json(jsonb,text) from public;
grant execute on function public.pfv_replace_retail_catalog_from_json(jsonb,text) to service_role;

commit;
