/** Listing and taxonomy types for AI List Assist frontend slices */

export interface AspectValue {
  name: string;
  value: string;
  required?: boolean;
}

export interface TaxonomyAspect {
  aspectName: string;
  aspectValues: string[];
  aspectRequired?: boolean;
  aspectMode?: string;
}

export interface ListingDraft {
  title: string;
  description: string;
  categoryId: string;
  categoryName?: string;
  condition: string;
  price: number;
  quantity: number;
  aspects: AspectValue[];
  images: string[];
  sku?: string;
}

export interface PricingStrategy {
  suggestedPrice: number;
  minPrice: number;
  maxPrice: number;
  confidence: number;
  rationale?: string;
}
