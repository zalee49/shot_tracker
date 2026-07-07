import { describe, expect, it } from "vitest";
import { brewRatio, ratioFlag } from "../coaching";
import { metricDeltas } from "../deltas";
import { parseGrindSize } from "../grind";
import { scoreSeriesByBean } from "../insights";
import {
  beanKey,
  coerceNumber,
  normalizeDate,
  normalizeShot,
  normalizeText,
  previousShotsById,
  savedBeanName,
  savedBeans,
  type Shot,
} from "../shots";

function shot(overrides: Partial<Shot>): Shot {
  return {
    id: null,
    date: null,
    bean_name: "",
    roaster: "",
    origin: "",
    roast_level: "",
    process_method: "",
    roast_date: null,
    dose: null,
    yield: null,
    brew_time: null,
    grind_size: "",
    grind_direction: "",
    temperature: null,
    rating: null,
    tasting_notes: "",
    ...overrides,
  };
}

describe("coaching (port of ratio_flag)", () => {
  it("computes the brew ratio", () => {
    expect(brewRatio(36, 18)).toBe(2);
    expect(brewRatio(36, 0)).toBeNull();
    expect(brewRatio(null, 18)).toBeNull();
  });

  it("flags on target within ±0.05", () => {
    expect(ratioFlag(36.9, 18, 2.0)?.message).toBe("On target");
    expect(ratioFlag(35.1, 18, 2.0)?.message).toBe("On target");
  });

  it("flags over and under with advice", () => {
    expect(ratioFlag(46, 17, 2.0)?.message).toBe(
      "Over by 0.71 — try less yield or more dose",
    );
    expect(ratioFlag(30, 18, 2.0)?.message).toBe(
      "Under by 0.33 — try more yield or less dose",
    );
  });
});

describe("normalization (port of normalize_shot)", () => {
  it("coerces numbers with bounds", () => {
    expect(coerceNumber("18.5")).toBe(18.5);
    expect(coerceNumber(true)).toBeNull();
    expect(coerceNumber(-1, { minimum: 0 })).toBeNull();
    expect(coerceNumber(11, { minimum: 1, maximum: 10 })).toBeNull();
    expect(coerceNumber(6.5, { integer: true })).toBeNull();
    expect(coerceNumber(Infinity)).toBeNull();
  });

  it("normalizes whitespace and dates", () => {
    expect(normalizeText("  Ethiopia   Yirgacheffe ")).toBe("Ethiopia Yirgacheffe");
    expect(normalizeDate("2026-07-06")).toBe("2026-07-06");
    expect(normalizeDate("2026-02-30")).toBeNull();
    expect(normalizeDate(12345)).toBeNull();
    expect(normalizeDate("")).toBeNull();
  });

  it("normalizes a full row and rejects non-objects", () => {
    const normalized = normalizeShot({
      id: 7,
      date: "2026-07-06",
      bean_name: " My  Bean ",
      rating: 11,
      dose: "18",
    });
    expect(normalized).toMatchObject({
      id: 7,
      date: "2026-07-06",
      bean_name: "My Bean",
      rating: null,
      dose: 18,
    });
    expect(normalizeShot("nope")).toBeNull();
    expect(normalizeShot(null)).toBeNull();
  });
});

describe("saved beans (port of get_saved_beans)", () => {
  it("dedupes case-insensitively, most recent wins", () => {
    const shots = [
      shot({ id: 3, bean_name: "Kenya AA", roaster: "New Roaster" }),
      shot({ id: 2, bean_name: "kenya aa", roaster: "Old Roaster" }),
      shot({ id: 1, bean_name: "Colombia" }),
    ];
    const beans = savedBeans(shots);
    expect(Array.from(beans.keys())).toEqual(["Kenya AA", "Colombia"]);
    expect(beans.get("Kenya AA")?.roaster).toBe("New Roaster");
    expect(beanKey("  Kenya  AA ")).toBe("kenya aa");
  });

  it("recovers the canonical saved bean display name", () => {
    const beanNames = ["Kenya AA", "Colombia"];
    expect(savedBeanName(beanNames, "  kenya   aa ")).toBe("Kenya AA");
    expect(savedBeanName(beanNames, "Brazil")).toBeNull();
    expect(savedBeanName(beanNames, "")).toBeNull();
  });

  it("supports stale selection fallbacks", () => {
    const beanNames = ["Kenya AA", "Colombia"];
    expect(savedBeanName(beanNames, "KENYA AA") ?? beanNames[0]).toBe("Kenya AA");
    expect(savedBeanName(beanNames, "Brazil") ?? beanNames[0]).toBe("Kenya AA");
    expect(savedBeanName(beanNames, "Brazil") ?? "__all__").toBe("__all__");
  });
});

describe("insights series", () => {
  it("combines score series by canonical bean name", () => {
    const series = scoreSeriesByBean([
      shot({ id: 3, date: "2026-07-03", bean_name: "Kenya AA", rating: 8 }),
      shot({ id: 2, date: "2026-07-02", bean_name: "Colombia", rating: 7 }),
      shot({ id: 1, date: "2026-07-01", bean_name: "kenya aa", rating: 6 }),
    ]);

    expect(Array.from(series.keys())).toEqual(["Kenya AA", "Colombia"]);
    expect(series.get("Kenya AA")?.map((point) => point.rating)).toEqual([6, 8]);
    expect(series.get("Kenya AA")?.every((point) => point.bean === "Kenya AA")).toBe(true);
  });
});

describe("previous shots (port of get_previous_shots_by_id)", () => {
  it("maps each shot to the previous shot of the same bean", () => {
    const shots = [
      shot({ id: 4, bean_name: "A", dose: 19 }),
      shot({ id: 3, bean_name: "B", dose: 15 }),
      shot({ id: 2, bean_name: "a", dose: 18 }),
      shot({ id: 1, bean_name: "A", dose: 17 }),
    ];
    const previous = previousShotsById(shots);
    expect(previous.get(1)).toBeNull();
    expect(previous.get(2)?.dose).toBe(17);
    expect(previous.get(3)).toBeNull();
    expect(previous.get(4)?.dose).toBe(18);
  });
});

describe("metric deltas (port of history_metric_grid)", () => {
  it("labels the first shot", () => {
    const deltas = metricDeltas(shot({ dose: 18 }), null);
    expect(deltas[0]).toMatchObject({ label: "Dose In", value: "18g", change: "First shot" });
  });

  it("computes signed changes and no-change", () => {
    const current = shot({ dose: 18, yield: 36, brew_time: 30, rating: 6 });
    const previous = shot({ dose: 17, yield: 46, brew_time: 30, rating: null });
    const [dose, yieldDelta, time, score] = metricDeltas(current, previous);
    expect(dose.change).toBe("+1g");
    expect(yieldDelta.change).toBe("−10g");
    expect(time.change).toBe("No change");
    expect(score.value).toBe("6/10");
    expect(score.change).toBe("No comparison");
  });
});

describe("grind parsing (port of parse_grind_size)", () => {
  it("extracts the first number from free text", () => {
    expect(parseGrindSize("11")).toBe(11);
    expect(parseGrindSize("2.5 turns")).toBe(2.5);
    expect(parseGrindSize(".75")).toBe(0.75);
    expect(parseGrindSize("-1.5")).toBe(-1.5);
    expect(parseGrindSize("coarse")).toBeNull();
    expect(parseGrindSize("")).toBeNull();
  });
});
