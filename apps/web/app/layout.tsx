import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import { ReasoningSidebar } from "@/components/ReasoningSidebar";
import OnboardingStepper from "@/components/OnboardingStepper";
import "./globals.css";

export const metadata: Metadata = {
  title: "DiscoverAI - Enterprise Knowledge Discovery",
  description: "AI-Powered technical architecture mapping and reasoning.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-background text-foreground antialiased selection:bg-primary/30 selection:text-primary-foreground min-h-screen">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex">
            <ReasoningSidebar />
            <main
              className="flex-1 transition-all duration-500 min-h-screen relative"
              style={{ paddingLeft: 'var(--sidebar-width)' }}
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