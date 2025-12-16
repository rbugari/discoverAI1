import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nexus Discovery",
  description: "Automated Data Lineage",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}