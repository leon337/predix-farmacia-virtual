import { createClient } from "npm:@supabase/supabase-js@2";

// Candidate predix-api v4 / semantic version 1.2.0.
const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
if (!SUPABASE_URL || !SERVICE_ROLE_KEY) throw new Error("Supabase runtime credentials unavailable");

const db = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { persistSession: false, autoRefreshToken: false },
});

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, idempotency-key",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Cache-Control": "no-store",
};

const productSelect = "id,sku,barcode,name,category,manufacturer,active_ingredient,presentation,price_cents,prescription_required,anvisa_registration,anvisa_process,registration_holder,holder_cnpj,source_url,source_mirror_url,source_updated_at,risk_class,identity_real,operations_simulated,image_url,image_source,image_verified_at,source_dataset,pfv_inventory(total,reserved,minimum)";

function response(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" },
  });
}

function fail(message: string, status = 400): Response {
  return response({ error: message, identityReal: true, operationsSimulated: true }, status);
}

function normalizeInventory(value: unknown): { total: number; reserved: number; minimum: number } {
  const raw = Array.isArray(value) ? value[0] : value;
  const item = (raw ?? {}) as Record<string, unknown>;
  return {
    total: Number(item.total ?? 0),
    reserved: Number(item.reserved ?? 0),
    minimum: Number(item.minimum ?? 0),
  };
}

function mapCompany(row: Record<string, unknown>) {
  return {
    id: row.id,
    name: row.name,
    address: row.address,
    phone: row.phone,
    openingHours: row.opening_hours,
    payments: row.payments,
    delivery: row.delivery,
    identityReal: false,
    operationsSimulated: true,
  };
}

function mapProduct(row: Record<string, unknown>) {
  const inventory = normalizeInventory(row.pfv_inventory);
  const hasPrice = row.price_cents !== null && row.price_cents !== undefined;
  const priceCents = hasPrice ? Number(row.price_cents) : null;
  const barcode = row.barcode ? String(row.barcode) : null;
  const anvisaRegistration = row.anvisa_registration ? String(row.anvisa_registration) : null;
  return {
    id: Number(row.id),
    sku: row.sku,
    barcode,
    name: row.name,
    category: row.category,
    manufacturer: row.manufacturer,
    activeIngredient: row.active_ingredient,
    presentation: row.presentation,
    priceCents,
    price: hasPrice
      ? new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(priceCents) / 100)
      : "Consulte o estabelecimento",
    priceAvailable: hasPrice,
    quantityTotal: inventory.total,
    quantityReserved: inventory.reserved,
    quantityAvailable: inventory.total - inventory.reserved,
    minimum: inventory.minimum,
    stockIsSimulated: true,
    prescriptionRequired: Boolean(row.prescription_required),
    anvisaRegistration,
    anvisaProcess: row.anvisa_process,
    registrationHolder: row.registration_holder,
    holderCnpj: row.holder_cnpj,
    sourceUrl: row.source_url,
    sourceMirrorUrl: row.source_mirror_url,
    sourceUpdatedAt: row.source_updated_at,
    riskClass: row.risk_class,
    imageUrl: row.image_url,
    imageSource: row.image_source,
    imageVerifiedAt: row.image_verified_at,
    sourceDataset: row.source_dataset,
    identitySource: barcode ? "gtin-and-open-beauty-facts" : anvisaRegistration ? "anvisa" : "catalog-source",
    identityReal: Boolean(row.identity_real),
    operationsSimulated: Boolean(row.operations_simulated),
  };
}

function safeQuery(value: string): string {
  return value.trim().slice(0, 100).replace(/[,%()]/g, " ").replace(/\s+/g, " ");
}

function extractProductTerm(message: string): string {
  const numericIdentity = message.match(/\b\d{8,20}\b/);
  if (numericIdentity) return numericIdentity[0];
  return safeQuery(
    message
      .replace(/\b(qual|quanto|custa|preço|preco|valor|tem|estoque|disponível|disponivel|produto|buscar|procure|reservar|reserve|reserva|registro|anvisa|codigo|código|barras|gtin|unidade|unidades|por|favor|do|da|de|o|a|os|as|em)\b/gi, " ")
      .replace(/[^\p{L}\p{N}\s-]+/gu, " "),
  );
}

async function getCompany() {
  const { data, error } = await db.from("pfv_company").select("*").limit(1).single();
  if (error) throw error;
  return mapCompany(data as Record<string, unknown>);
}

async function getProducts(query: string, page: number, pageSize: number) {
  const normalizedPage = Math.max(1, Math.trunc(page || 1));
  const normalizedSize = Math.min(100, Math.max(1, Math.trunc(pageSize || 24)));
  const from = (normalizedPage - 1) * normalizedSize;
  const to = from + normalizedSize - 1;
  let builder = db
    .from("pfv_products")
    .select(productSelect, { count: "exact" })
    .order("name", { ascending: true })
    .range(from, to);
  const term = safeQuery(query);
  if (term) {
    builder = builder.or(`name.ilike.%${term}%,sku.ilike.%${term}%,barcode.ilike.%${term}%,category.ilike.%${term}%,manufacturer.ilike.%${term}%,presentation.ilike.%${term}%,anvisa_registration.ilike.%${term}%`);
  }
  const { data, error, count } = await builder;
  if (error) throw error;
  const items = (data ?? []).map((row) => mapProduct(row as Record<string, unknown>));
  const total = Number(count ?? 0);
  return {
    items,
    page: normalizedPage,
    pageSize: normalizedSize,
    total,
    totalPages: Math.ceil(total / normalizedSize),
    firstRecord: total ? from + 1 : 0,
    lastRecord: Math.min(to + 1, total),
    distinctProducts: total,
    identityReal: items.length ? items.every((item) => item.identityReal) : null,
    operationsSimulated: true,
    pricesProvided: items.some((item) => item.priceAvailable),
  };
}

async function recordConversation(payload: {
  sessionId: string;
  userMessage: string;
  assistantMessage: string;
  intent: string;
  tool: string | null;
  sources: string[];
  handoff: boolean;
}) {
  const { error } = await db.from("pfv_conversations").insert({
    session_id: payload.sessionId,
    user_message: payload.userMessage,
    assistant_message: payload.assistantMessage,
    intent: payload.intent,
    tool: payload.tool,
    sources: payload.sources,
    handoff: payload.handoff,
  });
  if (error) console.error("conversation_record_failed", error.message);
}

async function handleChat(body: Record<string, unknown>): Promise<Response> {
  const message = String(body.message ?? "").trim().slice(0, 500);
  const sessionId = String(body.sessionId ?? crypto.randomUUID()).slice(0, 120);
  if (!message) return fail("Mensagem é obrigatória.");

  const lower = message.toLocaleLowerCase("pt-BR");
  let intent = "unsupported";
  let tool: string | null = null;
  let handoff = false;
  let sources: string[] = [];
  let assistantMessage = "";
  let data: Record<string, unknown> = {};
  const clinical = ["dose", "dosagem", "posologia", "diagnóstico", "diagnostico", "sintoma", "tratamento", "o que devo tomar", "qual remédio", "qual remedio"];

  if (clinical.some((item) => lower.includes(item))) {
    intent = "clinical_handoff";
    tool = "safety_policy";
    handoff = true;
    sources = ["treinamento/politicas.md"];
    assistantMessage = "Não posso orientar diagnóstico, tratamento, dosagem ou uso de medicamentos. A solicitação deve ser tratada por farmacêutico ou profissional de saúde humano.";
  } else if (["olá", "ola", "oi", "bom dia", "boa tarde", "boa noite"].some((item) => lower.includes(item))) {
    const company = await getCompany();
    intent = "greeting";
    tool = "get_company";
    sources = ["database:pfv_company", "treinamento/empresa.md"];
    assistantMessage = `Olá. Sou o Funcionário Virtual da ${company.name}. Posso consultar produtos reais por nome, marca ou código de barras, além do estoque demonstrativo, horários e reservas simuladas. Preços comerciais não estão cadastrados.`;
  } else if (["horário", "horario", "abre", "fecha", "funcionamento"].some((item) => lower.includes(item))) {
    const company = await getCompany();
    intent = "opening_hours";
    tool = "get_company";
    sources = ["database:pfv_company"];
    assistantMessage = `${company.openingHours}. Os dados da empresa são demonstrativos.`;
  } else if (["pagamento", "pix", "cartão", "cartao"].some((item) => lower.includes(item))) {
    const company = await getCompany();
    intent = "payments";
    tool = "get_company";
    sources = ["database:pfv_company", "treinamento/pagamentos.md"];
    assistantMessage = `${company.payments}. Nenhum pagamento real é processado.`;
  } else if (["entrega", "frete", "delivery"].some((item) => lower.includes(item))) {
    const company = await getCompany();
    intent = "delivery";
    tool = "get_company";
    sources = ["database:pfv_company", "treinamento/entregas.md"];
    assistantMessage = `${company.delivery}. A operação é simulada.`;
  } else if (["preço", "preco", "estoque", "disponível", "disponivel", "produto", "reserv", "registro", "anvisa", "barcode", "barras", "gtin"].some((item) => lower.includes(item))) {
    const term = extractProductTerm(message);
    const result = await getProducts(term, 1, 5);
    const product = result.items[0];
    tool = "search_products";
    sources = ["database:pfv_products", "database:pfv_inventory"];
    const { error: queryError } = await db.from("pfv_product_queries").insert({
      product_id: product?.id ?? null,
      query_text: term || message,
    });
    if (queryError) console.error("query_record_failed", queryError.message);

    if (!product) {
      intent = "product_not_found";
      handoff = true;
      assistantMessage = `Não encontrei “${term || "o produto informado"}” no catálogo.`;
    } else {
      if (product.barcode) sources.push(`gtin:${product.barcode}`);
      if (product.anvisaRegistration) sources.push(`anvisa:registro:${product.anvisaRegistration}`);
      if (product.sourceDataset) sources.push(`dataset:${product.sourceDataset}`);
      if (lower.includes("reserv")) {
        const quantityMatch = message.match(/\b(\d{1,3})\b/);
        const quantity = Math.max(1, Number(quantityMatch?.[1] ?? 1));
        intent = "reservation_prepare";
        assistantMessage = `${product.name} possui ${product.quantityAvailable} unidade(s) simulada(s) disponíveis. Preparei uma reserva simulada de ${quantity} unidade(s).`;
        data = { product, quantity };
      } else if (["preço", "preco", "valor", "custa"].some((item) => lower.includes(item))) {
        intent = "price_query";
        assistantMessage = product.priceAvailable
          ? `${product.name}: ${product.price}. O estoque e a operação permanecem simulados.`
          : `${product.name} é um produto real do catálogo. O preço comercial não está cadastrado neste protótipo; consulte o estabelecimento.`;
        data = { product };
      } else {
        intent = "stock_query";
        const identity = product.barcode
          ? `Código de barras: ${product.barcode}.`
          : product.anvisaRegistration
          ? `Registro Anvisa: ${product.anvisaRegistration}.`
          : "Identidade proveniente da fonte do catálogo.";
        assistantMessage = `${product.name}: ${product.quantityAvailable} unidade(s) simulada(s) disponíveis. ${identity}`;
        data = { product };
      }
    }
  } else {
    intent = "unsupported";
    tool = "handoff_policy";
    handoff = true;
    sources = ["treinamento/faq.md", "treinamento/politicas.md"];
    assistantMessage = "Não encontrei uma fonte autorizada para responder com segurança. A solicitação foi encaminhada para atendimento humano demonstrativo.";
  }

  await recordConversation({ sessionId, userMessage: message, assistantMessage, intent, tool, sources, handoff });
  return response({ message: assistantMessage, intent, tool, sources, handoffRequired: handoff, data, identityReal: true, operationsSimulated: true });
}

async function handleReports(): Promise<Response> {
  const [attendanceResult, reservationResult, handoffResult, inventoryResult, queriesResult, realResult, priceResult, imageResult, barcodeResult] = await Promise.all([
    db.from("pfv_conversations").select("id", { count: "exact", head: true }),
    db.from("pfv_reservations").select("id", { count: "exact", head: true }),
    db.from("pfv_conversations").select("id", { count: "exact", head: true }).eq("handoff", true),
    db.from("pfv_inventory").select("product_id,total,reserved"),
    db.from("pfv_product_queries").select("product_id").not("product_id", "is", null).limit(1000),
    db.from("pfv_products").select("id", { count: "exact", head: true }).eq("identity_real", true),
    db.from("pfv_products").select("id", { count: "exact", head: true }).is("price_cents", null),
    db.from("pfv_products").select("id", { count: "exact", head: true }).not("image_url", "is", null),
    db.from("pfv_products").select("id", { count: "exact", head: true }).not("barcode", "is", null),
  ]);
  const failures = [attendanceResult.error, reservationResult.error, handoffResult.error, inventoryResult.error, queriesResult.error, realResult.error, priceResult.error, imageResult.error, barcodeResult.error].filter(Boolean);
  if (failures.length) throw failures[0];

  const counts = new Map<number, number>();
  for (const item of queriesResult.data ?? []) {
    const id = Number(item.product_id);
    counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  const topIds = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10);
  let names = new Map<number, string>();
  if (topIds.length) {
    const { data, error } = await db.from("pfv_products").select("id,name").in("id", topIds.map(([id]) => id));
    if (error) throw error;
    names = new Map((data ?? []).map((item) => [Number(item.id), String(item.name)]));
  }

  const inventory = inventoryResult.data ?? [];
  return response({
    totalAttendances: Number(attendanceResult.count ?? 0),
    reservations: Number(reservationResult.count ?? 0),
    handoffs: Number(handoffResult.count ?? 0),
    outOfStockProducts: inventory.filter((item) => Number(item.total) - Number(item.reserved) <= 0).length,
    realIdentityProducts: Number(realResult.count ?? 0),
    distinctProducts: Number(realResult.count ?? 0),
    productsWithImages: Number(imageResult.count ?? 0),
    productsWithBarcode: Number(barcodeResult.count ?? 0),
    productsWithoutPrice: Number(priceResult.count ?? 0),
    stockUnitsSimulated: inventory.reduce((sum, item) => sum + Number(item.total ?? 0), 0),
    mostQueriedProducts: topIds.map(([id, queries]) => ({ name: names.get(id) ?? `Produto ${id}`, queries })),
    identityReal: true,
    operationsSimulated: true,
  });
}

async function health(): Promise<Response> {
  const [productsResult, realResult, priceResult, imageResult, barcodeResult, inventoryResult] = await Promise.all([
    db.from("pfv_products").select("id", { count: "exact", head: true }),
    db.from("pfv_products").select("id", { count: "exact", head: true }).eq("identity_real", true),
    db.from("pfv_products").select("id", { count: "exact", head: true }).is("price_cents", null),
    db.from("pfv_products").select("id", { count: "exact", head: true }).not("image_url", "is", null),
    db.from("pfv_products").select("id", { count: "exact", head: true }).not("barcode", "is", null),
    db.from("pfv_inventory").select("total,reserved"),
  ]);
  const error = productsResult.error || realResult.error || priceResult.error || imageResult.error || barcodeResult.error || inventoryResult.error;
  if (error) throw error;
  const productRecords = Number(productsResult.count ?? 0);
  const realProducts = Number(realResult.count ?? 0);
  const productsWithImages = Number(imageResult.count ?? 0);
  const distinctProducts = Number(barcodeResult.count ?? 0) || realProducts;
  const inventory = inventoryResult.data ?? [];
  const stockUnitsSimulated = inventory.reduce((sum, item) => sum + Number(item.total ?? 0), 0);
  return response({
    status: "ok",
    products: productRecords,
    productRecords,
    distinctProducts,
    realProducts,
    productsWithImages,
    productsWithBarcode: Number(barcodeResult.count ?? 0),
    productsWithoutPrice: Number(priceResult.count ?? 0),
    inventoryRows: inventory.length,
    stockUnitsSimulated,
    catalogIdentity: productRecords === 500 && realProducts === 500 && productsWithImages === 500 && Number(barcodeResult.count ?? 0) === 500
      ? "real-with-images"
      : "transition",
    productCountMeaning: "distinct-product-records",
    stockCountMeaning: "simulated-units",
    operations: "simulated",
    prices: "not-provided",
    database: "supabase-postgres",
    version: "1.2.0",
  });
}

Deno.serve(async (request: Request) => {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });
  try {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/predix-api/, "");
    if (request.method === "GET" && (path === "/api/health" || path === "/health" || path === "" || path === "/")) return await health();
    if (request.method === "GET" && path === "/api/company") return response(await getCompany());
    if (request.method === "GET" && path === "/api/products") return response(await getProducts(url.searchParams.get("query") ?? "", Number(url.searchParams.get("page") ?? 1), Number(url.searchParams.get("pageSize") ?? 24)));
    if (request.method === "POST" && path === "/api/chat") return await handleChat(await request.json());

    if (request.method === "POST" && path === "/api/reservations") {
      const body = await request.json() as Record<string, unknown>;
      const items = Array.isArray(body.items) ? body.items : [];
      const item = (items[0] ?? {}) as Record<string, unknown>;
      const { data, error } = await db.rpc("pfv_create_reservation", {
        p_customer_name: String(body.customerName ?? ""),
        p_contact: String(body.contact ?? ""),
        p_product_id: Number(item.productId),
        p_quantity: Number(item.quantity),
        p_idempotency_key: request.headers.get("Idempotency-Key") ?? "",
      });
      if (error) return fail(error.message);
      return response(data, 201);
    }

    const cancelMatch = path.match(/^\/api\/reservations\/([0-9a-f-]+)\/cancel$/i);
    if (request.method === "POST" && cancelMatch) {
      const { data, error } = await db.rpc("pfv_cancel_reservation", { p_reservation_id: cancelMatch[1] });
      if (error) return fail(error.message);
      return response(data);
    }

    if (request.method === "GET" && path === "/api/reports") return await handleReports();
    return fail("Rota não encontrada.", 404);
  } catch (error) {
    console.error("predix_api_error", error);
    return fail(error instanceof Error ? error.message : "Falha interna controlada.", 500);
  }
});
