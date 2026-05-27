(() => {
  if (typeof state === "undefined") return;
  if (globalThis.__AUTO_PACKAGE_FLOW_PATCHED) return;
  globalThis.__AUTO_PACKAGE_FLOW_PATCHED = true;

  // age-filter-patch already owns the same auto-package flow when it is loaded first.
  // Avoid wrapping inferStructure/setView twice, which makes the UI update once and then again.
  if (
    typeof inferStructure === "function" &&
    typeof setView === "function" &&
    inferStructure.name === "patchedInferStructure" &&
    setView.name === "patchedSetView"
  ) {
    return;
  }

  function hasStructuredCase() {
    return Boolean(state.structured);
  }

  function ensurePackageReady({ asyncRefresh = true, show = false } = {}) {
    if (!hasStructuredCase()) return;
    let needsRefresh = false;

    if (!Array.isArray(state.packages) || !state.packages.length) {
      generatePackagesLocal({ show });
      state.selectedPackageId = state.packages[0]?.id || null;
      needsRefresh = true;
    } else if (!state.selectedPackageId) {
      state.selectedPackageId = state.packages[0]?.id || null;
    }

    if (asyncRefresh && needsRefresh) {
      Promise.resolve(generatePackages({})).catch(() => {
        render();
      });
    }
  }

  const nativeInferStructure = inferStructure;
  inferStructure = async function patchedInferStructureAutoPackage(options = {}) {
    const nextView = options.goTo;
    await nativeInferStructure({ ...options, goTo: undefined });
    ensurePackageReady({ asyncRefresh: true, show: false });
    if (nextView) {
      setView(nextView);
    } else {
      render();
    }
  };

  const nativeInferStructureLocal = inferStructureLocal;
  inferStructureLocal = function patchedInferStructureLocalAutoPackage(options = {}) {
    const result = nativeInferStructureLocal(options);
    ensurePackageReady({ asyncRefresh: false, show: false });
    return result;
  };

  const nativeSetView = setView;
  setView = function patchedSetViewAutoPackage(view) {
    if ((view === "search" || view === "packages" || view === "report") && hasStructuredCase()) {
      ensurePackageReady({ asyncRefresh: view === "search", show: false });
    }
    return nativeSetView(view);
  };
})();
