"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  getRiskVariant,
  getStatusVariant,
  formatLabel,
} from "@/services/api";
import type { DocumentRecord } from "@/types";

export function ScreeningResultCard({ record }: { record: DocumentRecord }) {
  const extracted = record.extracted_data || {};
  const fields = Object.entries(extracted).filter(([k]) => k !== "mrz_valid" && k !== "file_path");

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            Document #{record.id}
            <Badge variant="secondary">{formatLabel(record.document_type)}</Badge>
          </CardTitle>
          <p className="text-sm text-muted-foreground">{record.filename}</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge variant={getRiskVariant(record.risk_level!)} className="uppercase">
            {record.risk_level || "unknown"} risk
          </Badge>
          <Badge variant={getStatusVariant(record.status)}>{formatLabel(record.status)}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="mb-1 flex justify-between text-sm">
            <span className="text-muted-foreground">Risk Score</span>
            <span className="font-semibold">
              {typeof record.risk_score === "number" ? record.risk_score.toFixed(1) : "—"} / 100
            </span>
          </div>
          <Progress value={record.risk_score} />
        </div>

        {fields.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-semibold">Extracted Data</h3>
            <div className="grid gap-2 sm:grid-cols-2">
              {fields.map(([key, value]) => (
                <div key={key} className="flex justify-between rounded border px-3 py-2 text-sm">
                  <span className="text-muted-foreground">{formatLabel(key)}</span>
                  <span className="font-medium">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {extracted.mrz_valid === false && (
          <Badge variant="destructive">MRZ checksum validation failed</Badge>
        )}

        <div className="grid gap-2 sm:grid-cols-3">
          <div className="rounded border p-3">
            <div className="text-xs text-muted-foreground">Tampering</div>
            <div className="mt-1 font-semibold">
              {record.has_tampering ? (
                <span className="text-red-500">
                  Suspected ({record.tampering_score.toFixed(1)}%)
                </span>
              ) : (
                <span className="text-emerald-600">
                  Clean ({record.tampering_score.toFixed(1)}%)
                </span>
              )}
            </div>
          </div>
          <div className="rounded border p-3">
            <div className="text-xs text-muted-foreground">Validation</div>
            <div className="mt-1 font-semibold">
              {record.is_valid ? (
                <span className="text-emerald-600">Valid</span>
              ) : (
                <span className="text-red-500">Issues ({record.validation_errors?.length ?? 0})</span>
              )}
            </div>
          </div>
          <div className="rounded border p-3">
            <div className="text-xs text-muted-foreground">Face Match</div>
            <div className="mt-1 font-semibold">
              {record.face_match ? (
                <span className="text-emerald-600">Match</span>
              ) : (
                <span className="text-red-500">No match</span>
              )}
            </div>
          </div>
        </div>

        {record.validation_errors && record.validation_errors.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-semibold">Validation Notes</h3>
            <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
              {record.validation_errors.slice(0, 6).map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
