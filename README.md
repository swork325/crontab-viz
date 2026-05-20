# crontab-viz

> Terminal dashboard that parses and visualizes crontab schedules with next-run countdowns

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Installation

```bash
pip install crontab-viz
```

Or install from source:

```bash
git clone https://github.com/yourusername/crontab-viz.git
cd crontab-viz && pip install .
```

---

## Usage

Run against your system crontab:

```bash
crontab-viz
```

Or point it at a specific crontab file:

```bash
crontab-viz --file /etc/cron.d/myjobs
```

The dashboard displays each cron entry with its schedule expression, a human-readable description, and a live countdown to the next execution.

```
┌─────────────────────────────────────────────────────┐
│  CRONTAB-VIZ  |  5 jobs loaded                      │
├──────────────────┬──────────────┬───────────────────┤
│ Schedule         │ Command      │ Next Run          │
├──────────────────┼──────────────┼───────────────────┤
│ */5 * * * *      │ backup.sh    │ in 3m 12s         │
│ 0 2 * * *        │ cleanup.py   │ in 14h 07m        │
│ 30 8 * * 1-5     │ report.sh    │ in 2d 01h         │
└──────────────────┴──────────────┴───────────────────┘
```

### Options

| Flag | Description |
|------|-------------|
| `--file` | Path to a crontab file |
| `--refresh` | Refresh interval in seconds (default: `5`) |
| `--no-color` | Disable colored output |

---

## License

[MIT](LICENSE) © 2024 crontab-viz contributors