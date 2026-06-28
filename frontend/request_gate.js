(function exposeRequestGate(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.HorticalcRequestGate = api;
  }
})(typeof window !== "undefined" ? window : globalThis, () => {
  function createLatestRequestGate() {
    let version = 0;
    return {
      reserve() {
        version += 1;
        return version;
      },
      invalidate() {
        version += 1;
      },
      isCurrent(requestVersion) {
        return requestVersion === version;
      },
    };
  }

  return { createLatestRequestGate };
});
