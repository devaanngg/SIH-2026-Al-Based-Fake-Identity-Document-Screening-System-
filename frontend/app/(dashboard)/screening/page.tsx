"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { UploadCloud, Loader2 } from "lucide-react";
import { screenDocument, getScreeningResult } from "@/services/api";
import { ScreeningResultCard } from "@/components/screening-result-card";
import type { DocumentRecord } from "@/types";

export default function ScreeningPage() {
  const router = useRouter();
  const [documentType, setDocumentType] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [livePhoto, setLivePhoto] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DocumentRecord | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!documentType || !file || loading) return;
    setLoading(true);
    try {
      const res = await screenDocument(documentType, file, livePhoto);
      const detail = await getScreeningResult(res.document_id);
      setResult(detail);
      router.refresh();
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "Screening failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">New Document Screening</h1>
        <p className="text-sm text-muted-foreground">
          Upload an identity document for AI-powered analysis
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
          <CardDescription>
            Supported: Passport, Visa, National ID, Driving License (JPG/PNG, max 10MB)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="doc-type">Document Type</Label>
              <Select value={documentType} onValueChange={setDocumentType}>
                <SelectTrigger id="doc-type">
                  <SelectValue placeholder="Select document type..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="passport">Passport</SelectItem>
                  <SelectItem value="visa">Visa</SelectItem>
                  <SelectItem value="national_id">National ID</SelectItem>
                  <SelectItem value="driving_license">Driving License</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="live-photo">Live Photo (optional face verification)</Label>
              <Input
                id="live-photo"
                type="file"
                accept="image/*"
                onChange={(e) => setLivePhoto(e.target.files?.[0] || null)}
              />
              <p className="text-xs text-muted-foreground">
                {livePhoto ? `${livePhoto.name} selected` : "Upload a current face photo to compare against the document portrait."}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="file">Document Image</Label>
              <label
                htmlFor="file"
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  const f = e.dataTransfer.files?.[0];
                  if (f) setFile(f);
                }}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
                  dragOver ? "border-primary bg-primary/5" : "border-border"
                }`}
              >
                <UploadCloud className="mb-3 h-10 w-10 text-muted-foreground" />
                <p className="text-sm font-medium">
                  {file ? file.name : "Click to upload or drag & drop"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {file
                    ? `${(file.size / 1024).toFixed(0)} KB — click to change`
                    : "JPG or PNG"}
                </p>
                <Input
                  id="file"
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </label>
            </div>

            <Button type="submit" disabled={!documentType || !file || loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="animate-spin" />
                  Screening...
                </>
              ) : (
                "Start Screening"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && <ScreeningResultCard record={result} />}
    </div>
  );
}
