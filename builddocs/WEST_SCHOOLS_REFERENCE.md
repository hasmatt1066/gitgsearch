# Western Region Schools Reference

Use this as a starting point for building `data/target_schools_west.json`.

---

## By Conference (2025-2026)

### Pac-12 (Remaining)
| School | State |
|--------|-------|
| Oregon State University | OR |
| Washington State University | WA |

### Big 12 (Western Schools)
| School | State |
|--------|-------|
| University of Arizona | AZ |
| Arizona State University | AZ |
| Brigham Young University | UT |
| University of Colorado | CO |
| University of Utah | UT |
| Colorado State University | CO |

### Big Ten (Western Schools)
| School | State |
|--------|-------|
| University of Oregon | OR |
| University of Washington | WA |
| University of Southern California | CA |
| University of California Los Angeles | CA |

### ACC (Western Schools)
| School | State |
|--------|-------|
| Stanford University | CA |
| University of California Berkeley | CA |

### Mountain West
| School | State |
|--------|-------|
| Air Force Academy | CO |
| Boise State University | ID |
| Colorado State University | CO |
| Fresno State University | CA |
| University of Hawaii | HI |
| University of Nevada Las Vegas | NV |
| University of Nevada Reno | NV |
| New Mexico State University | NM |
| San Diego State University | CA |
| San Jose State University | CA |
| University of New Mexico | NM |
| Utah State University | UT |
| University of Wyoming | WY |

### FCS Western Schools (Optional)
| School | State |
|--------|-------|
| UC Davis | CA |
| Cal Poly | CA |
| Sacramento State | CA |
| Montana State University | MT |
| University of Montana | MT |
| Northern Arizona University | AZ |
| Portland State University | OR |
| Idaho State University | ID |
| Weber State University | UT |

---

## Suggested Test Batch (5 Schools)

Start with a diverse mix:

```json
{
  "batch_name": "West Test Batch",
  "created": "2026-01-31",
  "schools": [
    {"name": "University of Colorado", "conference": "Big 12", "state": "CO", "priority": 1},
    {"name": "University of Oregon", "conference": "Big Ten", "state": "OR", "priority": 1},
    {"name": "San Diego State University", "conference": "Mountain West", "state": "CA", "priority": 2},
    {"name": "University of Wyoming", "conference": "Mountain West", "state": "WY", "priority": 2},
    {"name": "Boise State University", "conference": "Mountain West", "state": "ID", "priority": 1}
  ]
}
```

---

## Priority Suggestions

**Priority 1 (High):** Power conference schools, large programs
- Oregon, USC, UCLA, Washington, Colorado, Arizona State, Utah

**Priority 2 (Medium):** Mid-major programs with coaching turnover
- Mountain West schools, smaller Pac-12 remnants

**Priority 3 (Low):** FCS programs, smaller schools
- Only if capacity allows after higher priorities

---

## Notes

- Verify each school name matches or has alias in `data/school_aliases.json`
- Some schools may not have football programs (skip those)
- Conference realignment may affect this list - verify current conference
