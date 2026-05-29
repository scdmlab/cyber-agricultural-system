const baseUrl = import.meta.env.BASE_URL

export async function getAvailableFiles(crop, year) {
  const days = ["140", "156", "172", "188", "204", "220", "236", "252", "268", "284"]
  const availableDays = []
  for (const day of days) {
    const csvPath = `${baseUrl}20260306/result_${crop}/bnn_${day}/result_test_${year}_doy${day}.csv`
    try {
      const response = await fetch(csvPath)
      if (!response.ok) continue
      const text = await response.text()
      const firstLine = text.trim().split('\n')[0]
      if (firstLine.includes('predicted_yield') || firstLine.includes('FIPS')) {
        availableDays.push(day)
      }
    } catch {
      continue
    }
  }
  return availableDays
}