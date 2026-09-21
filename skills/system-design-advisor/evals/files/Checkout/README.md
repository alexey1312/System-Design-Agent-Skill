# Checkout service

Handles cart checkout for a marketplace. Sellers are paid out weekly.
Traffic: about 40 orders per minute on weekdays, 5x on sale days.
Decision log: we keep MySQL for orders because finance needs ACID and
the team knows it; this is deliberate.
