import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "GI Scribe | Clinical Dictation Assistant",
  description: "High-fidelity, HIPAA-compliant AI dictation station for Gastroenterology.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} selection:bg-indigo-100 selection:text-indigo-900`} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
