// Test básico en JavaScript para que Jest funcione
describe('Basic Test Suite', () => {
  test('should pass basic arithmetic', () => {
    expect(1 + 1).toBe(2);
    expect(2 * 3).toBe(6);
  });

  test('should verify string operations', () => {
    expect('hello'.toUpperCase()).toBe('HELLO');
    expect('world'.length).toBe(5);
  });

  test('should verify array operations', () => {
    const arr = [1, 2, 3];
    expect(arr.length).toBe(3);
    expect(arr).toContain(2);
  });

  test('should verify object properties', () => {
    const obj = { name: 'Tony', version: '2.0' };
    expect(obj.name).toBe('Tony');
    expect(obj).toHaveProperty('version');
  });
}); 