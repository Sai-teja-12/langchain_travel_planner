# Sample run: BLR → FCO

Command:

```bash
uv run travel-planner \
  --origin BLR \
  --destination FCO \
  --departure-date 2026-10-20 \
  --return-date 2026-10-25 \
  --travelers 2 \
  --preferences "food and museums"
```

LangSmith trace:
https://apac.smith.langchain.com/o/9b2bc8f7-793e-4011-b837-161e8c7d86f6/projects/p/5e3967db-799a-46bd-b483-1ffc823a0ac4/r/89de3f3b-d022-4315-8091-3f3c93c1fc7b?trace_id=89de3f3b-d022-4315-8091-3f3c93c1fc7b&start_time=2026-07-13T08:51:33.315070

---

```
Planning your trip...

  ✓  Hotels searched
  ✓  Destination researched
  ✓  Flights searched
  ✓  Itinerary built
  ✓  Budget calculated
  ✓  Trip plan assembled

══════════════════════════════════════════════════
  BLR → FCO  |  2026-10-20 to 2026-10-25  |  2 traveler(s)
══════════════════════════════════════════════════

Escape the bustle of Bengaluru for the golden "Ottobrate Romane" of Rome, where mild October days provide the perfect backdrop for a deep dive into the Eternal City’s history and flavors. Your journey begins with a seamless Etihad connection, setting the stage for five days of world-class art and culinary indulgence. Immerse yourselves in the masterpieces of the Borghese Gallery and the Doria Pamphilj, and take advantage of a rare "Free Sunday" at the Vatican Museums to witness the Sistine Chapel. Between iconic landmarks like the Colosseum and the Pantheon, you’ll savor Rome’s gastronomic soul through a guided food tour in Trastevere and a hands-on pasta-making class. Experience the modern pulse of the city at the Rome Film Fest before retreating to the comfort of premium accommodations like the Hilton Rome Airport or the luxurious QC Termeroma Spa. From the trendy wine bars of Monti to the legendary pizza at Bonci, this itinerary perfectly balances high-art exploration with the authentic tastes of Italy.

── Flights ──
  1. [OUT] Akasa Air / Etihad QP 590  BLR→FCO  10:00→18:20  $1,184.00 RT
  2. [OUT] Etihad EY 233  BLR→FCO  04:35→18:20  $1,276.00 RT
  3. [OUT] Etihad EY 239  BLR→FCO  22:15→06:25  $1,297.00 RT
  4. [RET] Etihad / Akasa Air EY 86  FCO→BLR  10:25→08:45  (RT fare on outbound)
  5. [RET] Etihad EY 86  FCO→BLR  10:25→03:00  (RT fare on outbound)
  6. [RET] Etihad EY 84  FCO→BLR  22:00→19:55  (RT fare on outbound)

── Hotels ──
  1. Air Rooms Rome Airport by HelloSky  ★4.2  $285.00/night
     Aeroporto Leonardo da Vinci, Terminal 1, 00054 Fiumicino RM, Italy
  2. Hilton Rome Airport  ★4.0  $245.00/night
     Via Arturo Ferrarin, 2, 00054 Fiumicino RM, Italy
  3. Hilton Garden Inn Rome Airport  ★4.1  $185.00/night
     Via Vittorio Bragadin, 2, 00054 Fiumicino RM, Italy
  4. QC Termeroma Spa and Resort  ★4.6  $410.00/night
     Via Portuense, 2178, 00054 Fiumicino RM, Italy
  5. Hotel Seccy Boutique Hotel  ★4.4  $155.00/night
     Via delle Scuole, 5, 00054 Fiumicino RM, Italy

── Itinerary ──

  2026-10-20
    • Arrival and Transfer to Rome ($14.00)
      Arrive at FCO at 18:20. Take the Leonardo Express train to Termini Station and check into your hotel in the Monti district.
    • Welcome Dinner in Monti ($40.00)
      Enjoy a traditional Roman dinner at Ai Tre Scalini, a popular wine bar and osteria known for its lasagna and local atmosphere.

  2026-10-21
    • Colosseum, Roman Forum, and Palatine Hill ($18.00)
      Explore the heart of Ancient Rome with a guided tour of the amphitheater and the ruins of the Roman Republic.
    • Lunch at La Taverna dei Fori Imperiali ($30.00)
      A family-run restaurant serving classic Roman dishes like Cacio e Pepe and Amatriciana.
    • Capitoline Museums ($16.00)
      Visit the world's oldest public museum to see the iconic Capitoline Wolf and the equestrian statue of Marcus Aurelius.
    • Dinner at Roscioli Salumeria con Cucina ($65.00)
      A world-famous deli and restaurant. Must try the Carbonara, often cited as the best in Rome.

  2026-10-22
    • Borghese Gallery and Gardens ($15.00)
      View masterpieces by Bernini, Caravaggio, and Canova in this stunning villa. Pre-booking is mandatory.
    • Lunch at Ginger Sapori e Salute ($25.00)
      A fresh, contemporary spot near the Spanish Steps offering high-quality organic Italian ingredients.
    • Spanish Steps and Trevi Fountain Walk ($0.00)
      A scenic walk through the historic center, stopping at the iconic fountain to toss a coin.
    • Trastevere Food Tour ($90.00)
      An evening guided walking tour through the cobblestone streets of Trastevere, sampling street food, cheeses, and local wines.

  2026-10-23
    • The Pantheon ($5.00)
      Visit the best-preserved monument of Ancient Rome, famous for its massive concrete dome and oculus.
    • National Roman Museum - Palazzo Massimo ($12.00)
      Discover one of the world's best collections of ancient art, including Roman frescoes and the 'Boxer at Rest' bronze statue.
    • Pizza al Taglio at Pizzarium Bonci ($20.00)
      Experience gourmet Roman pizza by the slice from legendary baker Gabriele Bonci.
    • Castel Sant'Angelo ($13.00)
      Explore the mausoleum of Emperor Hadrian turned papal fortress, offering panoramic views of the city.
    • Dinner at Hostaria Da Pietro ($50.00)
      A refined yet cozy restaurant near Piazza del Popolo serving traditional Roman-Jewish specialties.

  2026-10-24
    • Roman Pasta and Tiramisu Cooking Class ($85.00)
      A hands-on workshop where you learn to make fresh pasta from scratch and the perfect Tiramisu.
    • Doria Pamphilj Gallery ($15.00)
      Visit this private palace to see an incredible art collection including works by Velázquez and Titian in a lavish setting.
    • Rome Film Fest Event ($25.00)
      Attend a screening or red carpet event at the Auditorium Parco della Musica as part of the annual film festival.
    • Farewell Dinner in Testaccio ($55.00)
      Dine at Felice a Testaccio, a historic institution famous for its tableside-mixed Cacio e Pepe.

  2026-10-25
    • Vatican Museums and Sistine Chapel ($0.00)
      Take advantage of 'Free Sunday' (last Sunday of the month). Arrive very early to beat the crowds for the Sistine Chapel and Raphael Rooms.
    • St. Peter's Basilica ($0.00)
      Visit the largest church in the world and admire Michelangelo's Pietà.
    • Final Roman Lunch near Prati ($45.00)
      Enjoy a final meal at L'Arcangelo, known for its traditional Roman 'gnocchi' and refined appetizers.
    • Departure Transfer ($14.00)
      Take the Leonardo Express from Termini back to FCO for your 22:00 return flight.

── Budget ──
  Flights:     $1,184.00
  Hotels:      $1,425.00
  Activities:  $1,304.00
  Total:       $3,913.00

── Travel tips ──
  1. Apply for your Schengen Visa via VFS Global in Bengaluru at least 2-3 months before your October departure to ensure timely processing.
  2. Book tickets for the Borghese Gallery and Vatican Museums online weeks in advance to secure your preferred time slots and skip long lines.
  3. Use the Leonardo Express train for a 32-minute transfer from FCO to the city center and utilize the 'Tap & Go' contactless system for easy bus and metro travel.
  4. Stay vigilant against pickpockets in crowded tourist hotspots, particularly around Termini Station, the Colosseum, and on the Bus 64 route.
  5. Be prepared for massive crowds at the Vatican Museums on October 25th, as it coincides with the 'Free Sunday' monthly promotion.
```
