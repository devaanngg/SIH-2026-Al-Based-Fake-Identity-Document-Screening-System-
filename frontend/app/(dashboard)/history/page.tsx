"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  getScreeningHistory,
  getRiskVariant,
  getStatusVariant,
  formatLabel,
} from "@/services/api";
import { ScreeningResultCard } from "@/components/screening-result-card";
import type { DocumentRecord } from "@/types";

export default function HistoryPage() {
  const [records, setRecords] = useState<DocumentRecord[]>([]);
  const [selected, setSelected] = useState<DocumentRecord | null>(null);

  useEffect(() => {
    getScreeningHistory()
      .then(setRecords)
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Screening History</h1>
        <p className="text-sm text-muted-foreground">
          All processed documents and their risk assessments
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Documents ({records.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {records.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No screening records yet. Run your first screening.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-left text-xs text-muted-foreground">
                    <th className="px-4 py-3 font-medium">ID</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">Filename</th>
                    <th className="px-4 py-3 font-medium">Risk</th>
                    <th className="px-4 py-3 font-medium">Tampering</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((r) => (
                    <tr key={r.id} className="border-b hover:bg-muted/30">
                      <td className="px-4 py-3">#{r.id}</td>
                      <td className="px-4 py-3">{formatLabel(r.document_type)}</td>
                      <td className="max-w-[200px] truncate px-4 py-3">{r.filename}</td>
                      <td className="px-4 py-3">
                        <Badge variant={getRiskVariant(r.risk_level!)}>
                          {typeof r.risk_score === "number" ? r.risk_score.toFixed(0) : "—"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        {r.has_tampering ? "Yes" : "No"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={getStatusVariant(r.status)}>
                          {formatLabel(r.status)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button variant="outline" size="sm" onClick={() => setSelected(r)}>
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Detailed Screening Result</DialogTitle>
            <DialogDescription>
              Complete analysis for the selected document
            </DialogDescription>
          </DialogHeader>
          {selected && <ScreeningResultCard record={selected} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
