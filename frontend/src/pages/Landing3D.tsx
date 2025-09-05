import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Canvas, useFrame } from "@react-three/fiber";
import { useProgress } from "@react-three/drei";
import * as THREE from "three";
import { SEOHead } from "@/components/SEO";
import { Button } from "@/components/ui/button";

// Simple scene with a floating lens/drone motif, subtle grid, and idle/parallax motion
function LensScene({ visible }: { visible: boolean }) {
  const group = useRef<THREE.Group>(null!);
  const ring = useRef<THREE.Mesh>(null!);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const targetRot = useRef({ x: 0, y: 0 });
  const clock = useMemo(() => new THREE.Clock(), []);
  const [pageVisible, setPageVisible] = useState(true);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      const x = (e.clientX / innerWidth) * 2 - 1;
      const y = (e.clientY / innerHeight) * 2 - 1;
      setMouse({ x, y });
    };
    window.addEventListener("mousemove", onMove);
    const onVis = () => setPageVisible(!document.hidden);
    document.addEventListener("visibilitychange", onVis);
    return () => {
      window.removeEventListener("mousemove", onMove);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  useFrame(() => {
    if (!visible || !group.current) return;
    if (!pageVisible) return;

    const t = clock.getElapsedTime();

    // Idle oscillation
    group.current.position.y = Math.sin(t * 0.6) * 0.05;

    // Parallax
    targetRot.current.x = THREE.MathUtils.lerp(targetRot.current.x, mouse.y * 0.15, 0.05);
    targetRot.current.y = THREE.MathUtils.lerp(targetRot.current.y, mouse.x * 0.25, 0.05);
    group.current.rotation.x = targetRot.current.x;
    group.current.rotation.y = targetRot.current.y;

    // Ring rotation + scan pulse
    if (ring.current) {
      ring.current.rotation.z += 0.02;
      const pulse = (Math.sin(t * 2.2) + 1) / 2; // 0..1
      (ring.current.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.2 + pulse * 0.25;
    }
  });

  return (
    <group ref={group}>
      {/* Lens body */}
      <mesh castShadow position={[0, 0, 0]}>
        <icosahedronGeometry args={[0.4, 1]} />
        <meshStandardMaterial color={new THREE.Color("hsl(0,0%,85%)")} metalness={0.6} roughness={0.25} />
      </mesh>

      {/* Inner ring */}
      <mesh ref={ring} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.6, 0.03, 24, 128]} />
        <meshStandardMaterial color={new THREE.Color("hsl(210, 80%, 60%)")} emissive={new THREE.Color("hsl(210, 90%, 55%)")} emissiveIntensity={0.2} metalness={0.7} roughness={0.3} />
      </mesh>

      {/* Subtle glyphs */}
      <mesh position={[0.9, 0.1, -0.2]}>
        <sphereGeometry args={[0.03, 16, 16]} />
        <meshStandardMaterial color={new THREE.Color("hsl(20, 80%, 70%)")} emissiveIntensity={0.0} />
      </mesh>
      <mesh position={[-0.8, -0.15, 0.1]}>
        <boxGeometry args={[0.06, 0.01, 0.06]} />
        <meshStandardMaterial color={new THREE.Color("hsl(210, 20%, 70%)")} />
      </mesh>

      {/* Grid helper plane */}
      <gridHelper args={[8, 24, new THREE.Color("#ffffff").multiplyScalar(0.08), new THREE.Color("#ffffff").multiplyScalar(0.06)]} position={[0, -1.2, 0]} />
    </group>
  );
}

function LoaderOverlay() {
  const { active, progress } = useProgress();
  if (!active) return null;
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-background/60 backdrop-blur-sm">
      <div className="w-8 h-8 rounded-full border-2 border-muted-foreground/40 border-t-primary animate-spin" aria-label="Loading" />
      <div className="text-xs text-muted-foreground">Loading {Math.round(progress)}%</div>
    </div>
  );
}

function hasWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(
      (canvas.getContext("webgl") || canvas.getContext("experimental-webgl")) &&
      window?.WebGLRenderingContext
    );
  } catch {
    return false;
  }
}

const prefersReducedMotion = () => typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export type Landing3DProps = {
  onFinish?: () => void;
  onSkip?: () => void;
};

const Landing3D: React.FC<Landing3DProps> = ({ onFinish, onSkip }) => {
  const navigate = useNavigate();
  const [allowSkip, setAllowSkip] = useState(false);
  const [finished, setFinished] = useState(false);
  const [visible, setVisible] = useState(true);
  const [useStatic, setUseStatic] = useState(false);
  const liveRegionRef = useRef<HTMLDivElement>(null);

  // If already seen, go straight to upload unless QA forces replay
  useEffect(() => {
    const forceFallback = localStorage.getItem("ui.heroForceFallback") === "1";
    const replayBlocked = localStorage.getItem("ui.heroForceReplay") === "1"; // reserved if needed
    const seen = sessionStorage.getItem("hero.seen") === "1";
    const reduce = prefersReducedMotion();
    const noWebGL = !hasWebGL();
    setUseStatic(forceFallback || reduce || noWebGL);

    if (seen && !replayBlocked) {
      navigate("/upload", { replace: true });
    }
  }, [navigate]);

  // Skip becomes available after 1.5s
  useEffect(() => {
    const t = setTimeout(() => setAllowSkip(true), 1500);
    return () => clearTimeout(t);
  }, []);

  // Auto-finish after 3.5s (unless static, then we allow immediate continue)
  useEffect(() => {
    if (useStatic) return; // static waits for user
    const t = setTimeout(() => doFinish(), 3500);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useStatic]);

  const doFinish = () => {
    if (finished) return;
    setFinished(true);
    setVisible(false);
    sessionStorage.setItem("hero.seen", "1");
    if (liveRegionRef.current) liveRegionRef.current.textContent = "Welcome. Continue to upload.";
    if (onFinish) onFinish();
    else setTimeout(() => navigate("/upload", { replace: true }), 450);
  };

  const doSkip = () => {
    sessionStorage.setItem("hero.seen", "1");
    if (onSkip) onSkip();
    doFinish();
  };

  // Keyboard accessibility
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter" && allowSkip) doSkip();
      if (e.key === "Escape") doSkip();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [allowSkip]);

  return (
    <div className="relative min-h-[100dvh]" aria-label="Intro scene">
      <SEOHead title="Surveillance AI – 3D Landing Hero" description="Cinematic 3D intro with smooth handoff to Upload. Premium, soft gradient visuals." canonical={window.location.origin + "/"} />

      {/* Gradient background using semantic tokens */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--accent)) 100%)",
        }}
        aria-hidden
      />

      {/* Vignette */}
      <div className="pointer-events-none absolute inset-0 bg-black/10 dark:bg-black/30 [mask-image:radial-gradient(circle_at_center,black,transparent_70%)]" aria-hidden />

      {!useStatic ? (
        <div className="absolute inset-0">
          <Suspense fallback={<div />}> {/* real overlay below */}
            <Canvas
              dpr={[1, 1.8]}
              camera={{ position: [0, 0, 3.4], fov: 50 }}
              gl={{ antialias: true, powerPreference: "high-performance" }}
              style={{ opacity: visible ? 1 : 0, transition: "opacity 400ms ease" }}
            >
              <color attach="background" args={["transparent"]} />
              <ambientLight intensity={0.6} />
              <directionalLight position={[2, 3, 4]} intensity={1.1} />
              <directionalLight position={[-3, -2, -2]} intensity={0.3} />

              <LensScene visible={visible} />
            </Canvas>
            <LoaderOverlay />
          </Suspense>
        </div>
      ) : (
        // Static fallback with micro parallax via CSS (on hover/move)
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-[260px] h-[260px]">
            <div className="absolute inset-0 rounded-full shadow-[var(--shadow-elegant)]"
              style={{
                background: "radial-gradient(circle at 40% 40%, rgba(255,255,255,0.9), rgba(255,255,255,0.1) 60%, transparent 70%)",
              }}
              aria-hidden
            />
            <svg className="absolute inset-0" viewBox="0 0 100 100" role="img" aria-label="Lens">
              <circle cx="50" cy="50" r="28" fill="none" stroke="hsl(var(--foreground))" strokeOpacity="0.15" strokeWidth="0.6" />
              <circle cx="50" cy="50" r="22" fill="none" stroke="hsl(var(--primary))" strokeOpacity="0.6" strokeWidth="1.2" />
              <circle cx="50" cy="50" r="3" fill="hsl(var(--foreground))" fillOpacity="0.8" />
            </svg>
          </div>
        </div>
      )}

      {/* Skip/Continue */}
      <div className="absolute bottom-5 right-5 z-10">
        <Button
          variant="secondary"
          size="sm"
          onClick={doSkip}
          disabled={!allowSkip}
          aria-label={allowSkip ? "Continue" : "Please wait"}
        >
          {allowSkip ? "Continue" : "Loading"}
        </Button>
      </div>

      {/* Live region for screen readers */}
      <div ref={liveRegionRef} className="sr-only" aria-live="polite" role="status" />
    </div>
  );
};

export default Landing3D;
