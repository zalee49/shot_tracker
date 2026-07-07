"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { createShot, type ShotInput } from "@/actions/shots";
import { ratioFlag } from "@/lib/coaching";
import { PROCESS_METHODS, ROAST_LEVELS } from "@/lib/constants";
import type { Shot } from "@/lib/shots";
import { useTargetRatio } from "@/lib/useTargetRatio";
import { AdjustmentChips } from "./AdjustmentChips";
import { RatioCoach } from "./RatioCoach";

const NEW_BEAN = "__new__";

interface SavedBean {
  name: string;
  shot: Shot;
}

interface LogShotFormProps {
  beans: SavedBean[];
  lastShot: Shot | null;
  disabled: boolean;
}

interface BeanFields {
  name: string;
  roaster: string;
  origin: string;
  roastLevel: string;
  processMethod: string;
  roastDate: string;
}

function todayISO(): string {
  const now = new Date();
  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
  ].join("-");
}

function beanFieldsFrom(bean: SavedBean | null): BeanFields {
  if (!bean) {
    return {
      name: "",
      roaster: "",
      origin: "",
      roastLevel: "Light",
      processMethod: "Washed",
      roastDate: todayISO(),
    };
  }
  const { shot } = bean;
  return {
    name: bean.name,
    roaster: shot.roaster,
    origin: shot.origin,
    roastLevel: ROAST_LEVELS.includes(shot.roast_level as (typeof ROAST_LEVELS)[number])
      ? shot.roast_level
      : "Light",
    processMethod: PROCESS_METHODS.includes(
      shot.process_method as (typeof PROCESS_METHODS)[number],
    )
      ? shot.process_method
      : "Washed",
    roastDate: shot.roast_date ?? todayISO(),
  };
}

function defaultNumber(
  value: number | null,
  fallback: number,
  minimum: number,
  maximum: number,
): string {
  const number = value ?? fallback;
  return String(Math.min(Math.max(number, minimum), maximum));
}

function parseInput(value: string): number | null {
  if (value.trim() === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function LogShotForm({ beans, lastShot, disabled }: LogShotFormProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [targetRatio, setTargetRatio] = useTargetRatio();

  const initialBean = beans.length > 0 ? beans[0] : null;
  const [beanChoice, setBeanChoice] = useState(initialBean ? initialBean.name : NEW_BEAN);
  const [beanFields, setBeanFields] = useState<BeanFields>(() => beanFieldsFrom(initialBean));

  const [dose, setDose] = useState(() => defaultNumber(lastShot?.dose ?? null, 18, 0, 30));
  const [yieldG, setYieldG] = useState(() => defaultNumber(lastShot?.yield ?? null, 36, 0, 100));
  const [brewTime, setBrewTime] = useState(() =>
    defaultNumber(lastShot?.brew_time ?? null, 28, 0, 120),
  );
  const [temperature, setTemperature] = useState(() =>
    defaultNumber(lastShot?.temperature ?? null, 93, 80, 100),
  );
  const [grindSize, setGrindSize] = useState(lastShot?.grind_size ?? "");
  const [adjustments, setAdjustments] = useState<string[]>([]);
  const [rating, setRating] = useState(6);
  const [tastingNotes, setTastingNotes] = useState("");

  const isNewBean = beanChoice === NEW_BEAN;

  function handleBeanChange(choice: string) {
    setBeanChoice(choice);
    const bean = choice === NEW_BEAN ? null : beans.find((b) => b.name === choice) ?? null;
    setBeanFields(beanFieldsFrom(bean));
  }

  function setBeanField<Key extends keyof BeanFields>(key: Key, value: BeanFields[Key]) {
    setBeanFields((fields) => ({ ...fields, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const doseValue = parseInput(dose);
    const yieldValue = parseInput(yieldG);
    if (!beanFields.name.trim()) {
      toast.error("Add a bean name before logging this shot.");
      return;
    }
    if (doseValue === null || doseValue <= 0) {
      toast.error("Dose must be greater than zero.");
      return;
    }

    const input: ShotInput = {
      date: todayISO(),
      bean_name: beanFields.name,
      roaster: beanFields.roaster,
      origin: beanFields.origin,
      roast_level: beanFields.roastLevel as ShotInput["roast_level"],
      process_method: beanFields.processMethod as ShotInput["process_method"],
      roast_date: beanFields.roastDate,
      dose: doseValue,
      yield: yieldValue ?? 0,
      brew_time: Math.round(parseInput(brewTime) ?? 0),
      grind_size: grindSize,
      grind_direction: adjustments as ShotInput["grind_direction"],
      temperature: parseInput(temperature) ?? 93,
      rating,
      tasting_notes: tastingNotes,
    };

    startTransition(async () => {
      const result = await createShot(input);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      const ratio = (yieldValue ?? 0) / doseValue;
      const flag = ratioFlag(yieldValue, doseValue, targetRatio);
      toast.success(`Shot logged — brew ratio ${ratio.toFixed(2)}:1`, {
        description: flag?.message,
      });
      setAdjustments([]);
      setTastingNotes("");
      router.refresh();
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-end gap-2">
        <div className="min-w-0 flex-1 space-y-2">
          <Label htmlFor="bean-select">Bean</Label>
          <Select value={beanChoice} onValueChange={handleBeanChange}>
            <SelectTrigger id="bean-select" className="h-11 w-full bg-card">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NEW_BEAN}>New bean</SelectItem>
              {beans.map((bean) => (
                <SelectItem key={bean.name} value={bean.name}>
                  {bean.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="size-11 shrink-0 bg-card"
              title="Logging settings"
            >
              <SlidersHorizontal className="size-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-72 space-y-2">
            <Label htmlFor="target-ratio">Target brew ratio</Label>
            <Input
              id="target-ratio"
              type="number"
              inputMode="decimal"
              min={1}
              max={4}
              step={0.1}
              value={targetRatio}
              onChange={(event) => {
                const value = parseFloat(event.target.value);
                if (Number.isFinite(value)) setTargetRatio(value);
              }}
              className="h-10"
            />
            <p className="text-xs text-muted-foreground">
              A 1:2 ratio means 18g in and 36g out. Used for ratio guidance and the
              target line in Insights.
            </p>
          </PopoverContent>
        </Popover>
      </div>

      {isNewBean ? (
        <section className="space-y-4 rounded-xl border border-border bg-card p-4 shadow-xs">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Bean details
          </h2>
          <BeanDetailInputs fields={beanFields} setField={setBeanField} showName />
        </section>
      ) : (
        <div className="rounded-xl border border-border bg-card shadow-xs">
          <div className="flex items-center justify-between gap-3 p-4">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{beanFields.name}</p>
              <p className="truncate text-xs text-muted-foreground">
                {[beanFields.roaster, beanFields.origin, beanFields.processMethod]
                  .filter(Boolean)
                  .join(" · ") || "Saved bean details"}
              </p>
            </div>
            <span className="shrink-0 text-xs text-muted-foreground">Details reused</span>
          </div>
          <Collapsible>
            <CollapsibleTrigger asChild>
              <button
                type="button"
                className="w-full border-t border-border px-4 py-2.5 text-left text-xs font-medium text-primary hover:bg-muted/50"
              >
                Edit bean details
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="space-y-4 border-t border-border p-4">
                <BeanDetailInputs fields={beanFields} setField={setBeanField} showName={false} />
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      )}

      <section className="space-y-4 rounded-xl border border-border bg-card p-4 shadow-xs">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Recipe
        </h2>
        <div className="grid grid-cols-2 gap-3">
          <NumberField
            id="dose"
            label="Dose (g)"
            value={dose}
            onChange={setDose}
            min={0}
            max={30}
            step={0.1}
          />
          <NumberField
            id="yield"
            label="Yield (g)"
            value={yieldG}
            onChange={setYieldG}
            min={0}
            max={100}
            step={0.1}
          />
          <NumberField
            id="brew-time"
            label="Brew time (s)"
            value={brewTime}
            onChange={setBrewTime}
            min={0}
            max={120}
            step={1}
          />
          <NumberField
            id="temperature"
            label="Temperature (°C)"
            value={temperature}
            onChange={setTemperature}
            min={80}
            max={100}
            step={0.5}
          />
        </div>
        <RatioCoach
          dose={parseInput(dose)}
          yieldG={parseInput(yieldG)}
          targetRatio={targetRatio}
        />
        <div className="space-y-2">
          <Label htmlFor="grind-size">Grind size</Label>
          <Input
            id="grind-size"
            value={grindSize}
            onChange={(event) => setGrindSize(event.target.value)}
            placeholder="11 or 2.5 turns"
            className="h-11 bg-card"
          />
        </div>
        <div className="space-y-2">
          <Label>Adjustments vs last shot</Label>
          <AdjustmentChips selected={adjustments} onChange={setAdjustments} />
        </div>
      </section>

      <section className="space-y-4 rounded-xl border border-border bg-card p-4 shadow-xs">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Taste
        </h2>
        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <Label htmlFor="score">Score</Label>
            <span className="tnum text-sm font-semibold">{rating}/10</span>
          </div>
          <Slider
            id="score"
            min={1}
            max={10}
            step={1}
            value={[rating]}
            onValueChange={([value]) => setRating(value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="tasting-notes">Tasting notes</Label>
          <Textarea
            id="tasting-notes"
            value={tastingNotes}
            onChange={(event) => setTastingNotes(event.target.value)}
            placeholder="Sweetness, acidity, body, finish, and flavors"
            rows={3}
            className="bg-card"
          />
        </div>
      </section>

      <div className="sticky bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-30 -mx-4 bg-gradient-to-t from-background via-background/95 to-transparent px-4 pb-2 pt-4 md:static md:m-0 md:bg-none md:p-0">
        <Button
          type="submit"
          disabled={disabled || isPending}
          className="h-12 w-full text-[0.95rem] font-semibold shadow-sm"
        >
          {isPending ? "Logging…" : "Log Shot"}
        </Button>
        {disabled && (
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Logging is disabled until the database reconnects.
          </p>
        )}
      </div>
    </form>
  );
}

interface BeanDetailInputsProps {
  fields: BeanFields;
  setField: <Key extends keyof BeanFields>(key: Key, value: BeanFields[Key]) => void;
  showName: boolean;
}

function BeanDetailInputs({ fields, setField, showName }: BeanDetailInputsProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {showName && (
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="bean-name">Bean name</Label>
          <Input
            id="bean-name"
            value={fields.name}
            onChange={(event) => setField("name", event.target.value)}
            placeholder="Ethiopia Yirgacheffe"
            className="h-11 bg-card"
          />
        </div>
      )}
      <div className="space-y-2">
        <Label htmlFor="roaster">Roaster</Label>
        <Input
          id="roaster"
          value={fields.roaster}
          onChange={(event) => setField("roaster", event.target.value)}
          placeholder="Roaster name"
          className="h-11 bg-card"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="origin">Origin</Label>
        <Input
          id="origin"
          value={fields.origin}
          onChange={(event) => setField("origin", event.target.value)}
          placeholder="Yirgacheffe, Ethiopia"
          className="h-11 bg-card"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="roast-level">Roast level</Label>
        <Select
          value={fields.roastLevel}
          onValueChange={(value) => setField("roastLevel", value)}
        >
          <SelectTrigger id="roast-level" className="h-11 w-full bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ROAST_LEVELS.map((level) => (
              <SelectItem key={level} value={level}>
                {level}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="process-method">Process method</Label>
        <Select
          value={fields.processMethod}
          onValueChange={(value) => setField("processMethod", value)}
        >
          <SelectTrigger id="process-method" className="h-11 w-full bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PROCESS_METHODS.map((method) => (
              <SelectItem key={method} value={method}>
                {method}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="roast-date">Roast date</Label>
        <Input
          id="roast-date"
          type="date"
          value={fields.roastDate}
          onChange={(event) => setField("roastDate", event.target.value)}
          className="h-11 bg-card"
        />
      </div>
    </div>
  );
}

interface NumberFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  min: number;
  max: number;
  step: number;
}

function NumberField({ id, label, value, onChange, min, max, step }: NumberFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type="number"
        inputMode="decimal"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="tnum h-11 bg-card"
      />
    </div>
  );
}
