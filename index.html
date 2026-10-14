export interface DatabaseStatus {
  connected: boolean;
  message: string;
  target: string;
}

export interface HealthResponse {
  status: string;
  project: string;
  version: string;
  environment: string;
  timestamp: string;
  database: DatabaseStatus;
}

export interface CropBatch {
  id: number;
  batch_id: string;
  farmer_name: string;
  farmer_phone: string;
  crop_name: string;
  variety?: string;
  category?: string; // Grains, Oilseeds, Pulses, Vegetables, Cash Crops
  quantity_kg: number;
  available_qty_kg: number;
  price_per_kg: number;
  farm_location: string;
  mandi_name?: string;
  harvest_date: string;
  quality_grade: string;
  status: string;
  created_at: string;
}

export interface CropBatchUpdatePayload {
  quantity_kg?: number;
  price_per_kg?: number;
  farm_location?: string;
  harvest_date?: string;
  variety?: string;
  quality_grade?: string;
  status?: string;
}

export interface DirectBuyPayload {
  batch_id: string;
  buyer_name: string;
  buyer_phone?: string;
  quantity_kg: number;
  delivery_location: string;
}

export interface BuyerOrder {
  id: number;
  order_id: string;
  buyer_name: string;
  buyer_phone?: string;
  crop_name: string;
  required_qty_kg: number;
  fulfilled_qty_kg: number;
  max_price_per_kg: number;
  delivery_location: string;
  status: string; // Pending, Confirmed, In Transit, Delivered
  created_at: string;
}

export interface TradeMatch {
  id: number;
  match_id: string;
  batch_id: string;
  order_id: string;
  crop_name: string;
  matched_qty_kg: number;
  agreed_price_per_kg: number;
  total_value: number;
  status: string;
  is_anomaly: boolean;
  anomaly_score: number;
  anomaly_reason?: string;
  created_at: string;
}

export interface LogisticsStep {
  step: number;
  action: string;
  location: string;
  status: string;
  note: string;
}

export interface LogisticsRoute {
  id: number;
  route_id: string;
  match_id: string;
  batch_id: string;
  origin: string;
  destination: string;
  distance_km: number;
  estimated_hours: number;
  vehicle_type: string;
  cost_inr: number;
  co2_kg: number;
  transit_steps?: string;
  status: string;
  created_at: string;
}

// --- Phase 5 Logistics Optimization Types ---
export interface HubOption {
  hub_name: string;
  key: string;
  latitude: number;
  longitude: number;
}

export interface FleetSpecification {
  vehicle_type: string;
  capacity_kg: number;
  base_rate_inr: number;
  per_km_inr: number;
  avg_speed_kmh: number;
  co2_factor_kg_per_km: number;
  toll_estimate_inr: number;
  best_for: string;
}

export interface RouteCostBreakdown {
  base_booking_inr: number;
  distance_fare_inr: number;
  toll_estimate_inr: number;
  total_cost_inr: number;
  cost_per_kg_inr: number;
}

export interface EmissionMetrics {
  total_co2_kg: number;
  co2_per_kg_produce_grams: number;
  emission_factor_kg_per_km: number;
}

export interface RouteCalculationResponse {
  origin: string;
  destination: string;
  origin_hub: string;
  destination_hub: string;
  distance_km: number;
  estimated_hours: number;
  vehicle_type: string;
  vehicle_capacity_kg: number;
  payload_utilization_pct: number;
  cost_breakdown: RouteCostBreakdown;
  emission_metrics: EmissionMetrics;
  steps: LogisticsStep[];
}

export interface ConsolidationSavings {
  separate_shipments_cost_inr: number;
  consolidated_cost_inr: number;
  cost_saved_inr: number;
  savings_percentage: number;
}

export interface GreenEmissionsSavings {
  separate_co2_kg: number;
  consolidated_co2_kg: number;
  co2_saved_kg: number;
  co2_reduction_percentage: number;
}

export interface ConsolidationResponse {
  route_id: string;
  status: string;
  batches_consolidated: number;
  total_cargo_weight_kg: number;
  crops_included: string[];
  vehicle_assigned: string;
  payload_utilization_pct: number;
  destination: string;
  distance_km: number;
  estimated_hours: number;
  financial_savings: ConsolidationSavings;
  green_emissions_savings: GreenEmissionsSavings;
  individual_breakdowns: Array<{
    batch_id: string;
    crop: string;
    quantity_kg: number;
    origin: string;
    individual_cost_inr: number;
    individual_co2_kg: number;
  }>;
  transit_steps: LogisticsStep[];
}

export interface BlockchainBlock {
  index: number;
  block_hash: string;
  prev_hash: string;
  batch_id: string;
  event_type: string;
  actor: string;
  location: string;
  details: string;
  nonce: number;
  timestamp_str: string;
  timestamp: string;
}

export interface BlockchainVerifyResponse {
  chain_valid: boolean;
  total_blocks: number;
  ledger_type: string;
  message: string;
  tip_hash?: string;
}

export interface DemandEstimate {
  crop_name: string;
  total_supply_kg: number;
  total_demand_kg: number;
  supply_demand_ratio: number;
  market_sentiment: string;
  fair_mandi_benchmark_inr: number;
  recommended_min_price_inr: number;
  recommended_max_price_inr: number;
  demand_growth_pct: number;
  model_type: string;
}

export interface TraceabilityTimeline {
  batch: CropBatch;
  events: BlockchainBlock[];
  qr_code_payload: string;
  verification_status: string;
  chain_audit?: BlockchainVerifyResponse;
}

export interface ProvenanceEventPayload {
  batch_id: string;
  event_type: string;
  actor: string;
  location: string;
  details?: Record<string, any>;
}

// --- Phase 4 AI Market Intelligence Types ---
export interface TimelinePoint {
  date: string;
  label: string;
  demand_kg: number;
  type: string;
}

export interface DemandForecastResponse {
  crop_name: string;
  forecast_period_days: number;
  estimated_demand_kg: number;
  historical_orders_count: number;
  is_baseline_estimate: boolean;
  data_basis: string;
  confidence_note: string;
  timeline: TimelinePoint[];
  methodology: string;
}

export interface MspIntelligence {
  benchmark_available: boolean;
  msp_price_inr_per_kg: number | null;
  season: string;
  source: string;
  unit: string;
  status: 'ABOVE_MSP' | 'NEAR_MSP' | 'BELOW_MSP' | 'NO_OFFICIAL_MSP';
  diff_vs_msp_pct: number | null;
  status_summary: string;
}

export interface PriceIntelligenceResponse {
  crop_name: string;
  active_listings_count: number;
  price_data_available: boolean;
  min_price_inr: number;
  max_price_inr: number;
  average_price_inr: number;
  median_price_inr: number;
  msp_intelligence: MspIntelligence;
  legal_disclaimer: string;
}

export interface AnomalyAlert {
  alert_id: string;
  item_type: 'Listing' | 'Order';
  item_id: string;
  crop_name: string;
  actor_name: string;
  anomaly_category: string;
  observed_value: string;
  comparison_baseline: string;
  severity: 'High' | 'Medium' | 'Low';
  explanation: string;
  status: 'Active' | 'Reviewed' | 'Dismissed';
  created_at: string;
}

export interface CropAdvisoryContent {
  crop: string;
  optimal_moisture: string;
  storage_temperature: string;
  packaging_recommendation: string;
  pest_management: string;
  spoilage_risks: string;
  shelf_life: string;
}

export interface CropAdvisoryResponse {
  crop_query: string;
  language: 'en' | 'hi' | 'pa';
  advisory: CropAdvisoryContent;
  disclaimer: string;
}
