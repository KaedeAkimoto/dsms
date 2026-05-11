export const formatDateTime = (dateStr) => {
  if (!dateStr) {
    return '-'
  }
  
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      return dateStr
    }
    
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (error) {
    console.error('Date format error:', error)
    return dateStr
  }
}

/**
 * 将 UTC 时间转换为东八区时间（正确处理日期边界）
 * @param {string} dateStr - UTC 时间字符串（ISO格式或带Z后缀）
 * @returns {string} 东八区时间字符串
 */
export const formatUtcToCst = (dateStr) => {
  if (!dateStr) {
    return '-'
  }
  
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      return dateStr
    }
    
    // 获取UTC时间
    let year = date.getUTCFullYear()
    let month = date.getUTCMonth()
    let day = date.getUTCDate()
    let hours = date.getUTCHours()
    const minutes = date.getUTCMinutes()
    const seconds = date.getUTCSeconds()
    
    // 转换为东八区（UTC+8）
    hours += 8
    
    // 处理日期边界
    if (hours >= 24) {
      hours -= 24
      day += 1
      
      // 获取当月天数
      const daysInMonth = new Date(year, month + 1, 0).getDate()
      if (day > daysInMonth) {
        day = 1
        month += 1
        
        if (month > 11) {
          month = 0
          year += 1
        }
      }
    }
    
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')} ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  } catch (error) {
    console.error('Date format error:', error)
    return dateStr
  }
}

export const formatDate = (dateStr) => {
  if (!dateStr) {
    return '-'
  }
  
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      return dateStr
    }
    
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    
    return `${year}-${month}-${day}`
  } catch (error) {
    console.error('Date format error:', error)
    return dateStr
  }
}