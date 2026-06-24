import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AskTheMap — Ask any question about any place on Earth",
  description:
    "Select a location, ask a question, and get an AI-generated answer grounded in satellite imagery.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
