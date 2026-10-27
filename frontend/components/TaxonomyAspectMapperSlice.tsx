import React, { useState } from "react";
import type { ItemConditionEnum } from "../types/listing";

export interface AspectDefinition {
  name: string;
  mode: "SELECT" | "FREETEXT";
  values: string[];
}

interface Props {
  categoryId: string;
  requiredAspects: AspectDefinition[];
  recommendedAspects: AspectDefinition[];
  initialValues?: Record<string, string>;
  onSubmitNormalized: (aspects: Record<string, string[]>, conditionEnum: ItemConditionEnum) => void;
}

export const TaxonomyAspectMapperSlice: React.FC<Props> = ({
  categoryId,
  requiredAspects,
  recommendedAspects,
  initialValues = {},
  onSubmitNormalized,
}) => {
  const [values, setValues] = useState<Record<string, string>>(initialValues);
  const [condition, setCondition] = useState<ItemConditionEnum>("USED_EXCELLENT");

  const missingRequired = requiredAspects.filter((a) => !values[a.name]?.trim());

  const handleNormalizeAndSubmit = () => {
    const normalized: Record<string, string[]> = {};
    Object.entries(values).forEach(([k, v]) => {
      const trimmed = (v || "").trim().slice(0, 65);
      if (trimmed) normalized[k] = [trimmed];
    });
    onSubmitNormalized(normalized, condition);
  };

  return (
    <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-700">
          eBay Category #{categoryId} • REST Inventory Contract
        </span>
        <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
          {missingRequired.length === 0 ? "All Required Aspects Valid" : `${missingRequired.length} Required Missing`}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {requiredAspects.map((aspect) => (
          <div key={aspect.name}>
            <label className="block text-xs font-semibold text-rose-700 mb-1">
              {aspect.name} *
            </label>
            {aspect.mode === "SELECT" && aspect.values.length > 0 ? (
              <select
                value={values[aspect.name] || ""}
                onChange={(e) => setValues({ ...values, [aspect.name]: e.target.value })}
                className="w-full px-2.5 py-1.5 text-xs border rounded-lg"
              >
                <option value="">Select {aspect.name}...</option>
                {aspect.values.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                maxLength={65}
                value={values[aspect.name] || ""}
                onChange={(e) => setValues({ ...values, [aspect.name]: e.target.value })}
                className="w-full px-2.5 py-1.5 text-xs border rounded-lg"
              />
            )}
          </div>
        ))}
      </div>

      <button
        type="button"
        disabled={missingRequired.length > 0}
        onClick={handleNormalizeAndSubmit}
        className="px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-600 text-white disabled:bg-slate-300"
      >
        Validate & Normalize Aspects (Dict&lt;string, string[]&gt;)
      </button>
    </div>
  );
};
