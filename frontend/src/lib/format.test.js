import { fmtDate } from './format.js'

describe('fmtDate', () => {
  it('formate une date ISO en français', () => {
    const out = fmtDate('2026-09-01T09:00:00')
    expect(out).toMatch(/1 sept\.? 2026/)
    expect(out).toMatch(/09:00/)
  })
})
