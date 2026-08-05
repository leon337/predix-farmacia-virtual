begin;

alter table public.pfv_products
  drop constraint if exists pfv_products_name_key;

create unique index if not exists pfv_products_anvisa_identity_uidx
  on public.pfv_products (anvisa_registration, name, manufacturer)
  where anvisa_registration is not null;

insert into public.pfv_audit(actor,action,resource,after_json)
values (
  'manoel',
  'PRODUCT_IDENTITY_CONSTRAINT_CORRECTED',
  'pfv_products',
  jsonb_build_object(
    'removedConstraint','pfv_products_name_key',
    'identity','anvisa_registration + name + manufacturer'
  )
);

commit;
