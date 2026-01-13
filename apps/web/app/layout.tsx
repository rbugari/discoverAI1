import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google"; // [NEW] Import fonts
import { ThemeProvider } from "@/components/theme-provider";
import { ReasoningSidebar } from "@/components/ReasoningSidebar";
import OnboardingStepper from "@/components/OnboardingStepper";
import "./globals.css";

// [NEW] Configure fonts
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "DiggerAI - Enterprise Knowledge Discovery",
  description: "AI-Powered technical architecture mapping and reasoning.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${outfit.variable} font-sans bg-background text-foreground antialiased selection:bg-primary/30 selection:text-primary-foreground min-h-screen`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex">
            <ReasoningSidebar />
            <main
              className="flex-1 transition-all duration-500 h-screen relative font-sans overflow-hidden"
            >
              {children}
              <OnboardingStepper />
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}