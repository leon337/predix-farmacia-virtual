create or replace function public.pfv_create_reservation(
  p_customer_name text,
  p_contact text,
  p_product_id bigint,
  p_quantity integer,
  p_idempotency_key text
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
begin
  raise exception using message = 'Reservas públicas foram desativadas. Este ambiente oferece somente consulta informativa.';
end;
$$;

create or replace function public.pfv_cancel_reservation(
  p_reservation_id uuid
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
begin
  raise exception using message = 'Operações de reserva estão desativadas neste ambiente informativo.';
end;
$$;

revoke all on function public.pfv_create_reservation(text,text,bigint,integer,text) from public, anon, authenticated;
revoke all on function public.pfv_cancel_reservation(uuid) from public, anon, authenticated;

grant execute on function public.pfv_create_reservation(text,text,bigint,integer,text) to service_role;
grant execute on function public.pfv_cancel_reservation(uuid) to service_role;
