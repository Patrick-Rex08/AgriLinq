import {
  HealthResponse,
  CropBatch,
  BuyerOrder,
  TradeMatch,
  LogisticsRoute,
  BlockchainBlock,
  BlockchainVerifyResponse,
  DemandEstimate,
  TraceabilityTimeline,
  DemandForecastResponse,
  PriceIntelligenceResponse,
  AnomalyAlert,
  CropAdvisoryResponse,
  HubOption,
  FleetSpecification,
  RouteCalculationResponse,
  ConsolidationResponse,
  ProvenanceEventPayload
} from '../types';

const rawApiBase = import.meta.env.VITE_API_URL || '/api';
const API_BASE = rawApiBase.replace(/\/+$/, '');

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${cleanEndpoint}`;
  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      ...options,
    });

    if (!response.ok) {
      let errDetail = response.statusText;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errDetail = typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to statusText
      }
      throw new Error(`API ${response.status}: ${errDetail}`);
    }

    return await response.json();
  } catch (error) {
    throw new Error(
      error instanceof Error ? error.message : 'Unknown network or API error occurred.'
    );
  }
}

// --- Health Check ---
export async function fetchHealthStatus(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

// --- Crop Listings (Phase 3 Persistent API) ---
export interface ListingFilters {
  crop_name?: string;
  location?: string;
  category?: string;
  max_price?: number;
  sort_by?: string;
}

export async function fetchListings(filters?: ListingFilters): Promise<CropBatch[]> {
  const params = new URLSearchParams();
  if (filters?.crop_name) params.append('crop_name', filters.crop_name);
  if (filters?.location) params.append('location', filters.location);
  if (filters?.category && filters.category !== 'All') params.append('category', filters.category);
  if (filters?.max_price) params.append('max_price', filters.max_price.toString());
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);

  const query = params.toString() ? `?${params.toString()}` : '';
  return request<CropBatch[]>(`/listings${query}`);
}

// Alias for backwards compatibility
export const fetchCrops = (cropName?: string, _status?: string) => {
  return fetchListings(cropName ? { crop_name: cropName } : undefined);
};

export async function createCropListing(cropData: Partial<CropBatch>): Promise<CropBatch> {
  return request<CropBatch>('/listings', {
    method: 'POST',
    body: JSON.stringify(cropData),
  });
}
export const createCropBatch = createCropListing;

export async function getCropListing(identifier: string | number): Promise<CropBatch> {
  return request<CropBatch>(`/listings/${identifier}`);
}
export const getCropBatch = getCropListing;

export async function updateCropListing(identifier: string | number, data: Partial<CropBatch>): Promise<CropBatch> {
  return request<CropBatch>(`/listings/${identifier}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
export const updateCropBatch = updateCropListing;

export async function deleteCropListing(identifier: string | number): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>(`/listings/${identifier}`, {
    method: 'DELETE',
  });
}
export const deleteCropBatch = deleteCropListing;

// --- Buyer Orders (Phase 3 Persistent API) ---
export async function fetchBuyerOrders(): Promise<BuyerOrder[]> {
  return request<BuyerOrder[]>('/orders');
}

export async function placeBuyerOrder(orderData: {
  batch_id?: string;
  listing_id?: number;
  buyer_name: string;
  buyer_phone?: string;
  crop_name?: string;
  quantity_kg?: number;
  required_qty_kg?: number;
  price_per_kg?: number;
  max_price_per_kg?: number;
  delivery_location: string;
}): Promise<BuyerOrder> {
  const payload = {
    ...orderData,
    quantity_kg: orderData.quantity_kg ?? orderData.required_qty_kg ?? 0,
    price_per_kg: orderData.price_per_kg ?? orderData.max_price_per_kg ?? 0,
  };
  return request<BuyerOrder>('/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function buyListingDirect(payload: {
  batch_id: string;
  buyer_name: string;
  buyer_phone?: string;
  quantity_kg: number;
  delivery_location: string;
}): Promise<BuyerOrder> {
  return request<BuyerOrder>('/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateOrderStatus(orderId: string | number, status: string): Promise<BuyerOrder> {
  return request<BuyerOrder>(`/orders/${orderId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

// --- Demo Seeding Endpoint ---
export async function seedDemoData(force: boolean = false): Promise<{
  status: string;
  message: string;
  total_listings: number;
  total_orders: number;
}> {
  return request<{
    status: string;
    message: string;
    total_listings: number;
    total_orders: number;
  }>(`/seed${force ? '?force=true' : ''}`, {
    method: 'POST',
  });
}

// --- Phase 4 AI Market Intelligence API ---
export async function fetchDemandForecast(crop: string, days: number = 14): Promise<DemandForecastResponse> {
  return request<DemandForecastResponse>(`/ai/forecast?crop=${encodeURIComponent(crop)}&days=${days}`);
}

export async function fetchPriceIntelligence(crop: string): Promise<PriceIntelligenceResponse> {
  return request<PriceIntelligenceResponse>(`/ai/price-intelligence?crop=${encodeURIComponent(crop)}`);
}

export async function fetchAnomalyAlerts(): Promise<AnomalyAlert[]> {
  return request<AnomalyAlert[]>('/ai/anomalies');
}

export async function dismissAnomalyAlert(
  alertId: string,
  status: string = 'Dismissed',
  notes?: string
): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>(`/ai/anomalies/${encodeURIComponent(alertId)}/dismiss`, {
    method: 'PATCH',
    body: JSON.stringify({ status, notes }),
  });
}

export async function fetchCropAdvisory(crop: string, lang: string = 'en'): Promise<CropAdvisoryResponse> {
  return request<CropAdvisoryResponse>(`/ai/advisory?crop=${encodeURIComponent(crop)}&lang=${encodeURIComponent(lang)}`);
}

// --- Legacy Phase 1 / Future Phase Endpoints ---
export async function fetchMatches(): Promise<TradeMatch[]> {
  return request<TradeMatch[]>('/matches');
}

export async function triggerMatchingEngine(): Promise<TradeMatch[]> {
  return request<TradeMatch[]>('/matches/trigger', {
    method: 'POST',
  });
}

export async function fetchDemandEstimate(crop: string): Promise<DemandEstimate> {
  return request<DemandEstimate>(`/ai/demand-estimate?crop=${encodeURIComponent(crop)}`);
}

export async function fetchAnomalies(): Promise<TradeMatch[]> {
  return request<TradeMatch[]>('/ai/anomalies');
}

// --- Phase 5 Agricultural Logistics API ---
export async function fetchLogisticsRoutes(status?: string): Promise<LogisticsRoute[]> {
  const query = status ? `?status_filter=${encodeURIComponent(status)}` : '';
  return request<LogisticsRoute[]>(`/logistics${query}`);
}
export const fetchLogistics = fetchLogisticsRoutes;

export async function fetchLogisticsHubs(): Promise<HubOption[]> {
  return request<HubOption[]>('/logistics/hubs');
}

export async function fetchFleetSpecifications(): Promise<FleetSpecification[]> {
  return request<FleetSpecification[]>('/logistics/fleet');
}

export async function calculateRouteMetrics(payload: {
  origin: string;
  destination: string;
  cargo_weight_kg: number;
}): Promise<RouteCalculationResponse> {
  return request<RouteCalculationResponse>('/logistics/calculate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createDispatchRun(payload: {
  origin: string;
  destination: string;
  cargo_weight_kg: number;
  crop_name?: string;
  batch_id?: string;
}): Promise<LogisticsRoute> {
  return request<LogisticsRoute>('/logistics/dispatch', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function consolidateMultiFarm(payload: {
  batch_ids: string[];
  destination: string;
}): Promise<ConsolidationResponse> {
  return request<ConsolidationResponse>('/logistics/consolidate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateRouteStatus(routeId: string, status: string): Promise<LogisticsRoute> {
  return request<LogisticsRoute>(`/logistics/${encodeURIComponent(routeId)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export async function fetchBatchLogistics(batchId: string): Promise<LogisticsRoute[]> {
  return request<LogisticsRoute[]>(`/logistics/${batchId}`);
}

export async function fetchTraceability(batchId: string): Promise<TraceabilityTimeline> {
  return request<TraceabilityTimeline>(`/traceability/${batchId}`);
}

export async function fetchBlockchainBlocks(limit: number = 50): Promise<BlockchainBlock[]> {
  return request<BlockchainBlock[]>(`/blockchain/blocks?limit=${limit}`);
}

export async function verifyBlockchainLedger(): Promise<BlockchainVerifyResponse> {
  return request<BlockchainVerifyResponse>('/blockchain/verify');
}

export async function recordProvenanceEvent(payload: ProvenanceEventPayload): Promise<BlockchainBlock> {
  return request<BlockchainBlock>('/traceability/record-event', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
