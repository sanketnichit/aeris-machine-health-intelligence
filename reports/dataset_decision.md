# Dataset Choice

## Why I used AI4I 2020

I needed a dataset that was small enough to work with during the project but still had enough information to build a proper failure-prediction pipeline.

AI4I gives me:

- 10,000 rows
- a clear machine-failure target
- temperature, speed, torque and tool-wear inputs
- several failure-mode flags
- a fairly imbalanced target, so accuracy alone is not very useful
- a dataset size that is easy to reproduce locally

## Main limitation

AI4I is synthetic. It is useful for building and testing the project, but its results should not be treated as results from real factory equipment.

## Why I did not start with C-MAPSS

C-MAPSS is useful for temporal degradation and remaining-useful-life work, but that would push the project into a different problem. I wanted to get the basic failure-prediction pipeline working first.

## Why not a real industrial dataset

Real predictive-maintenance data is usually larger and more complicated, especially because time and machine history matter.

MetroPT-3 is one dataset I would try next. It has much more data and is closer to a real predictive-maintenance setting, but I did not need that extra complexity for the first version.

## One thing I want to keep clear

The AI4I results are only for this benchmark. I am not using them as evidence about Red Bull Powertrains or any other real machine fleet.
