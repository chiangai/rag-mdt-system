import { useState } from 'react'

const EXAMPLES = [
  '怀孕 24 周，糖耐量异常，伴随轻微水肿',
  '孕 32 周，血压 160/100mmHg，头痛，视物模糊，尿蛋白 2+',
  '孕 28 周，空腹血糖 6.2mmol/L，既往有糖尿病家族史，BMI 30',
  '孕 36 周，贫血，血红蛋白 85g/L，疲乏',
]

export default function ConsultInput({ onSubmit, disabled }) {
  const [complaint, setComplaint] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (complaint.trim() && !disabled) {
      onSubmit(complaint.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          患者主诉
        </label>
        <textarea
          value={complaint}
          onChange={(e) => setComplaint(e.target.value)}
          placeholder="请输入患者主诉，例如：怀孕 24 周，糖耐量异常，伴随轻微水肿"
          rows={3}
          disabled={disabled}
          className="w-full rounded-lg border border-gray-300 px-4 py-3 text-sm
                     focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none
                     disabled:bg-gray-50 disabled:text-gray-400
                     placeholder:text-gray-400 resize-none transition-all"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-gray-500 self-center mr-1">快速示例：</span>
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setComplaint(ex)}
            disabled={disabled}
            className="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-600
                       hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700
                       disabled:opacity-40 transition-all cursor-pointer"
          >
            {ex.length > 20 ? ex.slice(0, 20) + '…' : ex}
          </button>
        ))}
      </div>

      <button
        type="submit"
        disabled={disabled || !complaint.trim()}
        className="w-full py-3 rounded-lg font-medium text-white transition-all cursor-pointer
                   bg-blue-600 hover:bg-blue-700 active:bg-blue-800
                   disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {disabled ? '会诊进行中…' : '开始 MDT 会诊'}
      </button>
    </form>
  )
}
