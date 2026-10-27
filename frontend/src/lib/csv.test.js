import { csvCell, toCsv } from './csv.js'

describe('csvCell', () => {
  it.each(['=1+1', '+SUM(A1)', '-2', '@cmd', '\tx', '\rx'])('neutralise %j', (v) => {
    expect(csvCell(v)).toBe(`'${v}`)
  })
  it('laisse les valeurs sûres et gère null', () => {
    expect(csvCell('Acme')).toBe('Acme')
    expect(csvCell(12)).toBe('12')
    expect(csvCell(null)).toBe('')
  })
})

describe('toCsv', () => {
  it('cite, échappe les guillemets et neutralise les formules', () => {
    expect(toCsv([['a"b', '=HYPERLINK("x")'], [1, null]])).toBe(
      '"a""b","\'=HYPERLINK(""x"")"\n"1",""',
    )
  })
})
