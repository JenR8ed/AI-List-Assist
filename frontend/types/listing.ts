/**
 * Canonical TypeScript contracts mirroring shared/models.py and shared/schemas/pricing_strategy.py
 */

export type ItemConditionEnum =
  | "NEW"
  | "NEW_OTHER"
  | "NEW_WITH_DEFECTS"
  | "CERTIFIED_REFURBISHED"
  | "SELLER_REFURBISHED"
  | "USED_EXCELLENT"
  | "USED_GOOD"
  | "FOR_PARTS_OR_NOT_WORKING";

export type ProfitabilityLevel = "high" | "medium" | "low" | "not_recommended";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DetectedItem {
  item_id: string;
  bbox: BoundingBox;
  confidence: number;
  probable_category?: string;
  detected_text: string[];
  brand?: string;
  model?: string;
}

export interface ProfitBreakdown {
  list_price: number;
  ebay_fee_rate: number;
  ebay_fixed_fee: number;
  ebay_total_fee: number;
  shipping_cost: number;
  cogs: number;
  net_profit: number;
  net_margin_pct: number;
}

export interface ItemValuation {
  item_id: string;
  valuation_id?: string;
  item_name: string;
  brand?: string;
  estimated_age?: string;
  condition_score: number;
  condition_notes: string;
  is_complete: boolean;
  estimated_value: number;
  value_range: { low: number; high: number };
  resale_score: number;
  profitability: ProfitabilityLevel;
  recommended_platforms: string[];
  key_factors: string[];
  risks: string[];
  listing_tips: string[];
  worth_listing: boolean;
  confidence: number;
}

export interface ListingDraft {
  listing_id: string;
  item_id: string;
  title: string;
  description: string;
  category_id: string;
  condition: ItemConditionEnum;
  price: number;
  item_specifics: Record<string, string[]>;
  images: string[];
  confidence: number;
  ready_for_api: boolean;
}
