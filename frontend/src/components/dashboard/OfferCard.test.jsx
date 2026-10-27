import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import OfferCard from './OfferCard.jsx'

const future = (d) => new Date(Date.now() + d * 864e5).toISOString()
const base = {
  id: 1, kind: 'training', title: 'Formation X', provider_id: 2, provider_name: 'Acme',
  starts_at: future(5), ends_at: future(6), shared_seats: 10, booked_seats: 5,
  available_seats: 5, price_per_seat: 100, contact_phone: '0102030405', status: 'open', tags: [],
}
const show = (item, props = {}) =>
  render(
    <MemoryRouter>
      <OfferCard item={item} canBook onBook={() => {}} {...props} />
    </MemoryRouter>,
  )

describe('OfferCard indicateur de remplissage', () => {
  it.each([
    [5, '50% occupé', 'bg-green-500'],
    [6, '60% occupé', 'bg-amber-500'],
    [9, '90% occupé', 'bg-red-500'],
  ])('%i/10 places réservées', (booked, label, color) => {
    const { container } = show({ ...base, booked_seats: booked, available_seats: 10 - booked })
    expect(screen.getByText(label)).toBeInTheDocument()
    expect(container.querySelector('.fill-bar-fill')).toHaveClass(color)
    expect(container.querySelector('.fill-bar-fill').style.width).toBe(label.split('%')[0] + '%')
  })

  it('0% sans places partagées', () => {
    show({ ...base, shared_seats: 0, booked_seats: 0 })
    expect(screen.getByText('0% occupé')).toBeInTheDocument()
  })

  it("n'affiche pas la barre pour une salle", () => {
    show({ ...base, kind: 'room' })
    expect(screen.queryByText(/occupé$/)).toBeNull()
  })

  it('affiche Complète quand plus de place', () => {
    show({ ...base, booked_seats: 10, available_seats: 0 })
    expect(screen.getByText('Complète')).toBeInTheDocument()
  })
})
