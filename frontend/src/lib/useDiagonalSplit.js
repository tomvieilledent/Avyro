import { useEffect, useState } from 'react'

function compute(angleDeg) {
  const W = window.innerWidth
  const H = window.innerHeight
  const run = H / Math.tan((angleDeg * Math.PI) / 180)
  const xTop = W / 2 + run / 2
  const xBot = W / 2 - run / 2
  return {
    viewBox: `0 0 ${W} ${H}`,
    leftPoints: `0,0 ${xTop},0 ${xBot},${H} 0,${H}`,
    rightPoints: `${xTop},0 ${W},0 ${W},${H} ${xBot},${H}`,
    line: { x1: xTop, y1: 0, x2: xBot, y2: H },
  }
}

/** Recalcule la diagonale SVG plein écran (gauche/droite) au redimensionnement. */
export function useDiagonalSplit(angleDeg) {
  const [dims, setDims] = useState(() => compute(angleDeg))
  useEffect(() => {
    function onResize() {
      setDims(compute(angleDeg))
    }
    window.addEventListener('resize', onResize)
    onResize()
    return () => window.removeEventListener('resize', onResize)
  }, [angleDeg])
  return dims
}
