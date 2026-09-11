/*
  Preloadable fixed-time shim for Node.js
  - Enable with FIXED_TIME_ENABLED=true
  - Configure with FIXED_TIME_ISO (e.g., 2030-03-14T03:14:00-05:00)
  - Timezone via FIXED_TIME_ZONE (e.g., America/Chicago)
*/

try {
  const enabled = (process.env.FIXED_TIME_ENABLED || "").toLowerCase() === "true";
  if (!enabled) {
    return;
  }

  const fixedIso = process.env.FIXED_TIME_ISO || "2030-03-14T03:14:00-05:00";
  const fixedEpoch = Date.parse(fixedIso);
  if (!Number.isFinite(fixedEpoch)) {
    // Invalid configuration; do nothing
    return;
  }

  // Ensure Node timezone is consistent for formatting
  if (process.env.FIXED_TIME_ZONE && !process.env.TZ) {
    process.env.TZ = process.env.FIXED_TIME_ZONE;
  }

  const OriginalDate = Date;

  function DateOverride(...args) {
    // Called as a function returns a string representation
    if (!(this instanceof OriginalDate)) {
      return new OriginalDate(fixedEpoch).toString();
    }
    // Constructed with arguments -> behave normally
    if (args.length > 0) {
      return new OriginalDate(...args);
    }
    // No-arg constructor -> fixed time
    return new OriginalDate(fixedEpoch);
  }

  // Mirror static members
  Object.setPrototypeOf(DateOverride, OriginalDate);
  DateOverride.prototype = OriginalDate.prototype;
  DateOverride.now = () => fixedEpoch;
  DateOverride.parse = OriginalDate.parse;
  DateOverride.UTC = OriginalDate.UTC;

  // Proxy to correctly handle function and constructor behaviors
  const DateProxy = new Proxy(DateOverride, {
    apply(target, thisArg, argArray) {
      return String(new OriginalDate(fixedEpoch));
    },
    construct(target, argArray, newTarget) {
      return new OriginalDate(...(argArray.length > 0 ? argArray : [fixedEpoch]));
    },
  });

  // Install the shim
  // eslint-disable-next-line no-global-assign
  Date = DateProxy;
} catch (_e) {
  // Silently ignore to avoid crashing the app on misconfiguration
}



