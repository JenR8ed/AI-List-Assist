/**
 * TaxonomyAspectMapperSlice - maps eBay category aspects to listing form fields.
 * Placeholder / slice for future React migration.
 */
import React from "react";
import type { TaxonomyAspect, AspectValue } from "../types/listing";

interface Props {
  aspects: TaxonomyAspect[];
  values: AspectValue[];
  onChange: (values: AspectValue[]) => void;
}

export function TaxonomyAspectMapperSlice({ aspects, values, onChange }: Props) {
  const handleChange = (name: string, value: string) => {
    const next = values.filter((v) => v.name !== name);
    if (value) next.push({ name, value });
    onChange(next);
  };

  return (
    <div className="taxonomy-aspect-mapper">
      <h3>Category Aspects</h3>
      {aspects.map((a) => (
        <div key={a.aspectName} className="aspect-row">
          <label>
            {a.aspectName}
            {a.aspectRequired ? " *" : ""}
          </label>
          <select
            value={values.find((v) => v.name === a.aspectName)?.value ?? ""}
            onChange={(e) => handleChange(a.aspectName, e.target.value)}
          >
            <option value="">Select...</option>
            {a.aspectValues.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}

export default TaxonomyAspectMapperSlice;
