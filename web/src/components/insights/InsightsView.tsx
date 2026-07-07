"use client";

import { useMemo, useState } from "react";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  SERIES_COLORS,
  beanStats,
  beanTrend,
  ratioScorePoints,
  scoreSeriesByBean,
} from "@/lib/insights";
import { shotsForBean, type Shot } from "@/lib/shots";
import { useTargetRatio } from "@/lib/useTargetRatio";
import { ChartCard } from "./chart-theme";
import { RatioScoreScatter } from "./RatioScoreScatter";
import { ScoreOverTimeChart } from "./ScoreOverTimeChart";
import { TrendChart } from "./TrendChart";

interface InsightsViewProps {
  shots: Shot[];
  beanNames: string[];
}

export function InsightsView({ shots, beanNames }: InsightsViewProps) {
  const [selectedBean, setSelectedBean] = useState(beanNames[0]);
  const [targetRatio] = useTargetRatio();

  const scoreSeries = useMemo(() => {
    const byBean = scoreSeriesByBean(shots);
    return beanNames
      .map((bean, index) => ({
        bean,
        points: byBean.get(bean) ?? [],
        color: SERIES_COLORS[index % SERIES_COLORS.length],
      }))
      .filter((entry) => entry.points.length > 0);
  }, [shots, beanNames]);

  const beanShots = useMemo(
    () => shotsForBean(shots, selectedBean),
    [shots, selectedBean],
  );
  const stats = useMemo(() => beanStats(beanShots), [beanShots]);
  const beanColor =
    SERIES_COLORS[Math.max(beanNames.indexOf(selectedBean), 0) % SERIES_COLORS.length];

  const ratioTrend = useMemo(() => beanTrend(beanShots, "ratio", true), [beanShots]);
  const timeTrend = useMemo(() => beanTrend(beanShots, "brew_time"), [beanShots]);
  const ratingTrend = useMemo(() => beanTrend(beanShots, "rating", true), [beanShots]);
  const grindTrend = useMemo(() => beanTrend(beanShots, "grind"), [beanShots]);
  const scatterPoints = useMemo(() => ratioScorePoints(beanShots), [beanShots]);

  const hasTrendData =
    ratioTrend.length > 0 ||
    timeTrend.length > 0 ||
    ratingTrend.length > 0 ||
    grindTrend.length > 0;

  return (
    <div className="space-y-4">
      {scoreSeries.length > 0 && (
        <ChartCard
          title="Score over time — all beans"
          caption="Every rated shot, colored by bean, to track overall progress."
        >
          <ScoreOverTimeChart series={scoreSeries} />
        </ChartCard>
      )}

      <div className="space-y-2 pt-2">
        <Label htmlFor="insights-bean">Bean</Label>
        <Select value={selectedBean} onValueChange={setSelectedBean}>
          <SelectTrigger id="insights-bean" className="h-11 w-full bg-card sm:w-72">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {beanNames.map((name) => (
              <SelectItem key={name} value={name}>
                {name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-3 gap-2.5">
        <StatTile label="Shots logged" value={String(stats.shotCount)} />
        <StatTile label="Average score" value={stats.avgRating} />
        <StatTile label="Average ratio" value={stats.avgRatio} />
      </div>

      {!hasTrendData ? (
        <div className="rounded-xl border border-dashed border-input bg-card px-4 py-10 text-center text-sm text-muted-foreground">
          No valid recipe data is available for {selectedBean} yet.
        </div>
      ) : (
        <>
          <ChartCard
            title={`${selectedBean} trends`}
            caption="Each metric in its real units, oldest to newest."
          >
            <div className="space-y-5">
              <TrendChart
                title="Brew ratio"
                points={ratioTrend}
                color={beanColor}
                format={(value) => value.toFixed(2)}
                showRolling
              />
              <TrendChart
                title="Brew time (s)"
                points={timeTrend}
                color={beanColor}
                format={(value) => value.toFixed(0)}
              />
              <TrendChart
                title="Score"
                points={ratingTrend}
                color={beanColor}
                format={(value) => String(Math.round(value * 10) / 10)}
                showRolling
                domain={[0, 10]}
              />
              <TrendChart
                title="Grind size"
                points={grindTrend}
                color={beanColor}
                format={(value) => String(Math.round(value * 100) / 100)}
              />
            </div>
          </ChartCard>

          {scatterPoints.length > 0 && (
            <ChartCard
              title="Brew ratio vs. score"
              caption={`Each point is a ${selectedBean} shot — look for the ratio that clusters with your highest scores.`}
            >
              <RatioScoreScatter points={scatterPoints} targetRatio={targetRatio} />
            </ChartCard>
          )}
        </>
      )}
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-xl border border-border bg-card p-3.5 shadow-xs">
      <p className="text-[0.65rem] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="tnum mt-1 truncate text-lg font-bold tracking-tight sm:text-xl">
        {value}
      </p>
    </div>
  );
}
