export const flags = {
  enableExperimentalGoogleModel:
    (import.meta as any)?.env?.NEXT_PUBLIC_ENABLE_EXPERIMENTAL_GOOGLE_MODEL === "true" ||
    (import.meta as any)?.env?.VITE_ENABLE_EXPERIMENTAL_GOOGLE_MODEL === "true" ||
    true,
  enableLiveMock:
    (import.meta as any)?.env?.NEXT_PUBLIC_ENABLE_MOCKS === "true" ||
    (import.meta as any)?.env?.VITE_ENABLE_MOCKS === "true" ||
    ((import.meta as any)?.env?.DEV ? true : false),
  enableHighContrast:
    (import.meta as any)?.env?.NEXT_PUBLIC_ENABLE_HIGH_CONTRAST === "true" ||
    (import.meta as any)?.env?.VITE_ENABLE_HIGH_CONTRAST === "true" ||
    true,
};

export default flags;
