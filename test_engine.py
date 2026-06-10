import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from thermodynamics import calculate_state

print('=== 검증 테스트 ===\n')

# 테스트 1: T=100C 포화 혼합물 (h 입력)
print('[테스트 1] T=100C, h=2000 kJ/kg (포화 혼합물)')
r = calculate_state('T', 100.0, 'h', 2000.0)
phase = r['phase']
x_disp = r['x_display']
print(f'  상태: {phase}')
print(f'  건도: {x_disp}')
print(f'  T={r["T_C"]:.2f}C, P={r["P_kPa"]:.3f}kPa')
print(f'  v={r["v"]:.5f}, u={r["u"]:.3f}, h={r["h"]:.3f}, s={r["s"]:.4f}')
print()

# 테스트 2: T=150C, h=2745.9 (포화증기에 근접)
print('[테스트 2] T=150C, h=2745.9 kJ/kg (포화증기 근접)')
r = calculate_state('T', 150.0, 'h', 2745.9)
print(f'  상태: {r["phase"]}')
print(f'  건도: {r["x_display"]}')
print()

# 테스트 3: P=476.16kPa, h=1500
print('[테스트 3] P=476.16 kPa, h=1500 kJ/kg (포화 혼합물)')
r = calculate_state('P', 476.16, 'h', 1500.0)
print(f'  상태: {r["phase"]}')
print(f'  건도: {r["x_display"]}')
print(f'  T={r["T_C"]:.2f}C, P={r["P_kPa"]:.3f}kPa')
print()

# 테스트 4: 압축액
print('[테스트 4] T=100C, h=50 kJ/kg (압축액)')
r = calculate_state('T', 100.0, 'h', 50.0)
print(f'  상태: {r["phase"]}')
print(f'  건도: {r["x_display"]}')
print()

# 테스트 5: 과열증기
print('[테스트 5] T=100C, h=3000 kJ/kg (과열증기)')
r = calculate_state('T', 100.0, 'h', 3000.0)
print(f'  상태: {r["phase"]}')
print(f'  건도: {r["x_display"]}')
print(f'  T={r["T_C"]:.2f}C, P={r["P_kPa"]:.3f}kPa, h={r["h"]:.3f}')
print()

print('=== 모든 테스트 완료 ===')
