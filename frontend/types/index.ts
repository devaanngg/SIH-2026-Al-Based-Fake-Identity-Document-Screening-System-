export type RiskLevel = "low" | "medium" | "high" | "critical";
export type DocumentType = "passport" | "visa" | "national_id" | "driving_license";

export interface ExtractedData {
  name?: string;
  passport_number?: string;
  nationality?: string;
  date_of_birth?: string;
  date_of_expiry?: string;
  gender?: string;
  visa_number?: string;
  visa_type?: string;
  document_number?: string;
  mrz_valid?: boolean;
  [key: string]: string | boolean | undefined;
}

export interface DocumentRecord {
  id: number;
  document_type: string;
  filename: string;
  upload_time: string;
  extracted_data: ExtractedData | null;
  is_valid: boolean;
  validation_errors: string[] | null;
  tampering_score: number;
  has_tampering: boolean;
  face_match_score: number;
  face_match: boolean;
  risk_score: number;
  risk_level: RiskLevel | null;
  status: "screening" | "cleared" | "flagged" | "review" | "approved" | "rejected";
  notes?: string | null;
}

export interface DashboardStats {
  total_documents: number;
  flagged_documents: number;
  high_risk_count: number;
  average_processing_time: number;
  documents_by_type: Record<string, number>;
  risk_distribution: Record<string, number>;
}
