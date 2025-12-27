# Fan Control - Manual Alternatives

## ⚠️ NBFC Discontinued

The [NBFC (NoteBook FanControl)](https://github.com/hirschmann/nbfc) project has been discontinued and is no longer maintained. Direct fan control via software on Windows is very limited.

---

## 🔧 Alternative Solutions

### Option 1: Manufacturer Software ⭐ **Recommended**

Most laptop manufacturers provide fan control in their utilities:

#### ASUS Laptops
**Armoury Crate** or **MyASUS**
- Download from Windows Store or ASUS website
- Navigate to Fan Settings
- Set to "Performance" or "Turbo" mode
- Enable "Start with Windows"

#### MSI Laptops
**MSI Dragon Center** or **MSI Center**
- Download from MSI website
- Go to System Performance
- Select "Extreme Performance" fan profile
- Save settings

#### Lenovo Laptops
**Lenovo Vantage**
- Download from Windows Store
- Thermal Settings → Performance Mode
- Enable "Always On AC Power" mode

#### Dell Laptops
**Dell Power Manager**
- Download from Dell Support
- Thermal Management → Ultra Performance
- Apply settings

#### HP Laptops
**HP Omen Gaming Hub** (gaming) or **HP Command Center**
- Performance Mode
- Fan Control → Maximum
- Apply

---

### Option 2: BIOS Settings ⚡

**Most reliable method** but varies by manufacturer:

1. **Restart PC**
2. **Press F2/Del/F12** (depends on manufacturer) to enter BIOS
3. **Find**:
   - "Fan Control"
   - "Thermal Settings"
   - "Advanced Settings"
4. **Set to**:
   - "Performance"
   - "Full Speed"
   - "Maximum"
5. **Save and Exit** (F10)

**Pros:**
- ✅ Works at OS level (before Windows loads)
- ✅ Most reliable
- ✅ No software needed

**Cons:**
- ❌ Can't change on-the-fly
- ❌ Fans always 100% (loud!)

---

### Option 3: Third-Party Tools (Use at Your Own Risk)

Some alternatives to NBFC exist but are less tested:

#### Fan Control (by Rem0o)
- GitHub: https://github.com/Rem0o/FanControl.Releases
- Modern UI
- Plugin support
- **Active development** ✅

**Installation:**
1. Download latest release
2. Install and run as Administrator
3. Configure fan curves
4. Enable "Start minimized"

#### SpeedFan (Legacy)
- Very old but still works on some systems
- Limited modern laptop support
- Not recommended for newer systems

---

## 💡 Recommendations

### For Gaming/Heavy Work:
```
Manufacturer Software → Performance Mode
+
Windows Optimizer @ 85% CPU
=
Optimal cooling + performance
```

### For Silent Operation:
```
Manufacturer Software → Balanced Mode
+
Windows Optimizer @ 85% CPU
=
Quiet + cool enough
```

### Maximum Cooling:
```
BIOS → Full Speed Fans
+
Windows Optimizer @ 85% CPU
+
Good laptop stand/cooling pad
=
Coldest possible
```

---

## 🔍 Why Software Fan Control is Limited on Windows

1. **Security**: Microsoft restricts low-level hardware access
2. **Drivers**: Manufacturer-specific EC (Embedded Controller) protocols
3. **Liability**: Incorrect fan control can damage hardware
4. **Variety**: Every laptop model has different EC implementations

**Result**: Manufacturer software is the most reliable option.

---

## ✅ Recommended Setup

For the **Windows NVMe RAM Optimizer**, we recommend:

1. **CPU @ 85%** (via optimizer) ✅
2. **RAM Cleaning** (via optimizer) ✅
3. **Fan Control** (via manufacturer software) 🔧

**Example with ASUS:**
```
1. Install Windows Optimizer
2. Install ASUS Armoury Crate
3. Set Armoury Crate → Performance Mode
4. Enable both to start with Windows
```

**Result:**
- CPU: 75-80°C (vs 95°C)
- Fans: 100% via ASUS software
- RAM: Auto-cleaned
- System: Optimized!

---

## 🎯 Summary

| Method | Reliability | Ease | Flexibility |
|--------|-------------|------|-------------|
| **Manufacturer Software** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **BIOS Settings** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Fan Control (Rem0o)** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **NBFC** | ❌ | ❌ | ❌ |

---

**Use manufacturer software for best results!**
