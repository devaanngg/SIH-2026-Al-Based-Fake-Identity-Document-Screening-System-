import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocGuard AI — Document Screening",
  description: "AI-powered identity document screening and verification system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
