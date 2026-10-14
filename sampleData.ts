import { CropBatch, BuyerOrder } from '../types';

export const INITIAL_SAMPLE_BATCHES: Partial<CropBatch>[] = [
  {
    batch_id: 'BATCH-WHT-2026-001',
    farmer_name: 'Ramesh Kumar (Kisan FPO)',
    farmer_phone: '9876543210',
    crop_name: 'Wheat',
    variety: 'Sharbati Gold',
    category: 'Grains & Cereals',
    quantity_kg: 5000,
    available_qty_kg: 3200,
    price_per_kg: 25.5,
    farm_location: 'Karnal, Haryana',
    mandi_name: 'Karnal Grain Mandi',
    harvest_date: '2026-10-05',
    quality_grade: 'Grade A',
    status: 'LISTED',
  },
  {
    batch_id: 'BATCH-RIC-2026-002',
    farmer_name: 'Gurpreet Singh',
    farmer_phone: '9812345678',
    crop_name: 'Basmati Rice',
    variety: 'Pusa 1121 Extra Long',
    category: 'Grains & Cereals',
    quantity_kg: 4000,
    available_qty_kg: 4000,
    price_per_kg: 46.0,
    farm_location: 'Ludhiana, Punjab',
    mandi_name: 'Ludhiana Agro Hub',
    harvest_date: '2026-10-02',
    quality_grade: 'Export Quality',
    status: 'LISTED',
  },
  {
    batch_id: 'BATCH-MUS-2026-003',
    farmer_name: 'Sita Ram Sharma',
    farmer_phone: '9823456789',
    crop_name: 'Mustard',
    variety: 'Pusa Bold High Oil',
    category: 'Oilseeds & Pulses',
    quantity_kg: 3000,
    available_qty_kg: 1800,
    price_per_kg: 56.5,
    farm_location: 'Jaipur, Rajasthan',
    mandi_name: 'Jaipur Krishi Upaj Mandi',
    harvest_date: '2026-10-08',
    quality_grade: 'Grade A',
    status: 'LISTED',
  },
  {
    batch_id: 'BATCH-SOY-2026-004',
    farmer_name: 'Devendra Yadav (Malwa Farmers FPO)',
    farmer_phone: '9834567890',
    crop_name: 'Soybean',
    variety: 'JS 335 Yellow',
    category: 'Oilseeds & Pulses',
    quantity_kg: 6000,
    available_qty_kg: 6000,
    price_per_kg: 44.0,
    farm_location: 'Indore, Madhya Pradesh',
    mandi_name: 'Indore Central Mandi',
    harvest_date: '2026-10-06',
    quality_grade: 'Grade A',
    status: 'LISTED',
  },
  {
    batch_id: 'BATCH-ONI-2026-005',
    farmer_name: 'Kisan Baburao Patil',
    farmer_phone: '9845678901',
    crop_name: 'Onion',
    variety: 'Nashik Red Globe',
    category: 'Vegetables & Spices',
    quantity_kg: 8000,
    available_qty_kg: 5500,
    price_per_kg: 24.0,
    farm_location: 'Nashik, Maharashtra',
    mandi_name: 'Lasalgaon Onion Mandi',
    harvest_date: '2026-10-09',
    quality_grade: 'Grade A',
    status: 'LISTED',
  },
  {
    batch_id: 'BATCH-COT-2026-006',
    farmer_name: 'Manish Patel',
    farmer_phone: '9856789012',
    crop_name: 'Cotton',
    variety: 'Bt Cotton Long Staple',
    category: 'Cash Crops',
    quantity_kg: 4500,
    available_qty_kg: 4500,
    price_per_kg: 68.0,
    farm_location: 'Rajkot, Gujarat',
    mandi_name: 'Rajkot APMC Market',
    harvest_date: '2026-10-04',
    quality_grade: 'Export Quality',
    status: 'LISTED',
  },
];

export const INITIAL_SAMPLE_ORDERS: Partial<BuyerOrder>[] = [
  {
    order_id: 'ORD-2026-101',
    buyer_name: 'Delhi Flour & Milling Co.',
    buyer_phone: '9123456781',
    crop_name: 'Wheat',
    required_qty_kg: 1800,
    fulfilled_qty_kg: 1800,
    max_price_per_kg: 25.5,
    delivery_location: 'Azadpur Mandi, Delhi',
    status: 'In Transit',
  },
  {
    order_id: 'ORD-2026-102',
    buyer_name: 'Jaipur Edible Oils Refinery',
    buyer_phone: '9123456782',
    crop_name: 'Mustard',
    required_qty_kg: 1200,
    fulfilled_qty_kg: 1200,
    max_price_per_kg: 56.5,
    delivery_location: 'Sitapura Industrial Area, Jaipur',
    status: 'Confirmed',
  },
  {
    order_id: 'ORD-2026-103',
    buyer_name: 'Mumbai Wholesale Vegetable Mart',
    buyer_phone: '9123456783',
    crop_name: 'Onion',
    required_qty_kg: 2500,
    fulfilled_qty_kg: 2500,
    max_price_per_kg: 24.0,
    delivery_location: 'Vashi APMC Market, Navi Mumbai',
    status: 'Delivered',
  },
];

export function getCropCategory(cropName: string): string {
  const c = cropName.trim().toLowerCase();
  if (['wheat', 'rice', 'basmati rice', 'maize', 'barley', 'millet'].some(g => c.includes(g))) {
    return 'Grains & Cereals';
  }
  if (['mustard', 'soybean', 'groundnut', 'chana', 'gram', 'moong', 'urad'].some(o => c.includes(o))) {
    return 'Oilseeds & Pulses';
  }
  if (['onion', 'tomato', 'potato', 'garlic', 'ginger', 'chilli'].some(v => c.includes(v))) {
    return 'Vegetables & Spices';
  }
  if (['cotton', 'sugarcane', 'jute', 'tobacco'].some(k => c.includes(k))) {
    return 'Cash Crops';
  }
  return 'Grains & Cereals';
}
