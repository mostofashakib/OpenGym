import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import Script from "next/script"
import { RandomizationProvider } from "@/lib/randomization-context"
import { ThemeVars } from "@/components/theme-vars"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "Gmail Clone",
  description: "A Gmail clone for AI agent evaluation and benchmarking",
  generator: 'v0.app'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} antialiased`}>
      <body className="font-sans">
        <Script id="fixed-time-shim" strategy="beforeInteractive">
          {`
            (function(){
              try {
                var enabled = ${process.env.NEXT_PUBLIC_FIXED_TIME_ENABLED ? "true" : "false"};
                var isDev = ${process.env.NODE_ENV === "development" ? "true" : "false"};
                if (!enabled) return;
                var fixedIso = ${JSON.stringify(process.env.NEXT_PUBLIC_FIXED_TIME_ISO || "2030-03-14T03:14:00-05:00")};
                var tz = ${JSON.stringify(process.env.NEXT_PUBLIC_FIXED_TIME_ZONE || "America/Chicago")};
                var fixedEpoch = Date.parse(fixedIso);
                if (!Number.isFinite(fixedEpoch)) return;

                if (!isDev) {
                  var OriginalDate = Date;
                  function DateOverride() {
                    var args = Array.prototype.slice.call(arguments);
                    if (!(this instanceof OriginalDate)) {
                      return new OriginalDate(fixedEpoch).toString();
                    }
                    if (args.length > 0) {
                      return new OriginalDate(...args);
                    }
                    return new OriginalDate(fixedEpoch);
                  }
                  Object.setPrototypeOf(DateOverride, OriginalDate);
                  DateOverride.prototype = OriginalDate.prototype;
                  DateOverride.now = function() { return fixedEpoch; };
                  DateOverride.parse = OriginalDate.parse;
                  DateOverride.UTC = OriginalDate.UTC;
                  window.Date = new Proxy(DateOverride, {
                    apply: function(target, thisArg, argArray) { return String(new OriginalDate(fixedEpoch)); },
                    construct: function(target, argArray, newTarget) { return Reflect.construct(OriginalDate, (argArray && argArray.length > 0) ? argArray : [fixedEpoch], newTarget); }
                  });
                }

                // Force timezone to America/Chicago for formatting when not provided
                var OriginalDateTimeFormat = Intl.DateTimeFormat;
                var PatchedDateTimeFormat = function(locale, options){
                  options = options || {};
                  if (!options.timeZone) options.timeZone = tz;
                  return new OriginalDateTimeFormat(locale, options);
                };
                PatchedDateTimeFormat.prototype = OriginalDateTimeFormat.prototype;
                PatchedDateTimeFormat.supportedLocalesOf = OriginalDateTimeFormat.supportedLocalesOf.bind(OriginalDateTimeFormat);
                Intl.DateTimeFormat = PatchedDateTimeFormat;

                var originalResolved = OriginalDateTimeFormat.prototype.resolvedOptions;
                OriginalDateTimeFormat.prototype.resolvedOptions = function(){
                  var o = originalResolved.call(this);
                  o.timeZone = tz;
                  return o;
                };
              } catch (e) {}
            })();
          `}
        </Script>
        <RandomizationProvider>
          <ThemeVars>
            {children}
          </ThemeVars>
        </RandomizationProvider>
      </body>
    </html>
  )
}
