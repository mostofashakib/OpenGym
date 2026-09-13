/*
  Preloadable fixed-time shim for Node.js and browser environment in OpenGym
  Synchronizes Date.now() with virtual simulation epoch.
*/

try {
  const enabled = (typeof process !== "undefined" && (process.env.FIXED_TIME_ENABLED || "").toLowerCase() === "true") ||
                  (typeof window !== "undefined" && !!window.__OPENGYM_VIRTUAL_EPOCH__);

  const fixedEpoch = typeof process !== "undefined" && process.env.FIXED_TIME_ISO
    ? Date.parse(process.env.FIXED_TIME_ISO)
    : (typeof window !== "undefined" && window.__OPENGYM_VIRTUAL_EPOCH__ ? window.__OPENGYM_VIRTUAL_EPOCH__ : 1792054800000); // 2026-10-15T09:00:00Z

  if (Number.isFinite(fixedEpoch)) {
    const OriginalDate = Date;

    function DateOverride(...args) {
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
    DateOverride.now = () => fixedEpoch;
    DateOverride.parse = OriginalDate.parse;
    DateOverride.UTC = OriginalDate.UTC;

    const DateProxy = new Proxy(DateOverride, {
      apply(target, thisArg, argArray) {
        return String(new OriginalDate(fixedEpoch));
      },
      construct(target, argArray, newTarget) {
        return new OriginalDate(...(argArray.length > 0 ? argArray : [fixedEpoch]));
      },
    });

    // eslint-disable-next-line no-global-assign
    Date = DateProxy;
  }
} catch (e) {
  // Silent fallback
}
