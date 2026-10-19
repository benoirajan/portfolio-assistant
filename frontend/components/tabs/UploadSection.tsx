'use client'

import React, { useState, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  X,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  FileText,
  Info,
} from 'lucide-react'
import { uploadHoldingsFile } from '@/lib/api'
import type { UploadHoldingsResponse } from '@/lib/types'

interface UploadSectionProps {
  onUploadSuccess?: (res: UploadHoldingsResponse) => void
  onClose?: () => void
  isCollapsible?: boolean
}

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 // 5 MB

const fmtCurrency = (n?: number) => {
  if (n == null || isNaN(n)) return '—'
  return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function UploadSection({
  onUploadSuccess,
  onClose,
  isCollapsible = false,
}: UploadSectionProps) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [result, setResult] = useState<UploadHoldingsResponse | null>(null)
  const [showSkipped, setShowSkipped] = useState(false)
  const [showFormatGuide, setShowFormatGuide] = useState(false)

  const validateAndSetFile = (file: File) => {
    setUploadError(null)
    setResult(null)

    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!ext || !['csv', 'xlsx', 'xls'].includes(ext)) {
      setUploadError('Unsupported file type. Please upload a .csv or .xlsx file.')
      setSelectedFile(null)
      return
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setUploadError('File is too large. Maximum allowed size is 5 MB.')
      setSelectedFile(null)
      return
    }

    setSelectedFile(file)
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadError(null)

    try {
      const response = await uploadHoldingsFile(selectedFile)
      setResult(response)

      // Invalidate portfolio queries to trigger instant re-fetch across the dashboard
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['holdings'] }),
        queryClient.invalidateQueries({ queryKey: ['performance'] }),
        queryClient.invalidateQueries({ queryKey: ['tax'] }),
        queryClient.invalidateQueries({ queryKey: ['advisory'] }),
      ])

      if (onUploadSuccess) {
        onUploadSuccess(response)
      }
    } catch (err: unknown) {
      let message = 'Upload failed. Please try again.'
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        message = axiosErr.response?.data?.detail || message
      } else if (err instanceof Error) {
        message = err.message
      }
      setUploadError(message)
    } finally {
      setIsUploading(false)
    }
  }

  const handleReset = () => {
    setSelectedFile(null)
    setResult(null)
    setUploadError(null)
    setShowSkipped(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 shadow-sm transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[var(--blue)]/10 text-[var(--blue)] flex items-center justify-center">
            <FileSpreadsheet size={18} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[var(--text)]">Import Holdings</h3>
            <p className="text-xs text-[var(--muted)]">
              Upload Zerodha export, Groww, or any custom CSV/Excel spreadsheet
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowFormatGuide((prev) => !prev)}
            className="flex items-center gap-1 text-xs text-[var(--muted)] hover:text-[var(--text)] transition-colors px-2 py-1 rounded border border-[var(--border)]"
            title="View column formatting guidelines"
          >
            <Info size={13} />
            <span className="hidden sm:inline">Format Guide</span>
          </button>
          {isCollapsible && onClose && (
            <button
              type="button"
              onClick={onClose}
              className="text-[var(--muted)] hover:text-[var(--text)] p-1 rounded-md transition-colors"
              aria-label="Close upload section"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Format Guide Drawer */}
      {showFormatGuide && (
        <div className="mb-4 p-3.5 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-xs text-[var(--muted)] space-y-2 animate-fadeIn">
          <div className="font-semibold text-[var(--text)] flex items-center justify-between">
            <span>Supported Columns & Aliases:</span>
            <span className="text-[10px] font-normal text-[var(--muted)]">Required: Symbol, Qty, Avg Price</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="font-medium text-[var(--text)]">Symbol:</span> tradingsymbol, symbol, stock, ticker, scrip
            </div>
            <div>
              <span className="font-medium text-[var(--text)]">Quantity:</span> quantity, qty, shares, units
            </div>
            <div>
              <span className="font-medium text-[var(--text)]">Avg Price:</span> average_price, avg_price, buy_price, avg_cost
            </div>
            <div>
              <span className="font-medium text-[var(--text)]">LTP / Current:</span> last_price, ltp, cmp, market_price
            </div>
            <div>
              <span className="font-medium text-[var(--text)]">Exchange:</span> exchange, exch, market (defaults to NSE)
            </div>
            <div>
              <span className="font-medium text-[var(--text)]">P&L:</span> pnl, profit, profit_loss (calculated if missing)
            </div>
          </div>
          <p className="text-[10px] text-[var(--muted)] pt-1 border-t border-[var(--border)]">
            Supported extensions: <code>.csv</code>, <code>.xlsx</code>, <code>.xls</code> (Max size: 5 MB). Uploading replaces previous manual portfolio data and invalidates cached analytics.
          </p>
        </div>
      )}

      {/* Main Upload / Success States */}
      {!result ? (
        <div className="space-y-4">
          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 ${
              isDragging
                ? 'border-[var(--blue)] bg-[var(--blue)]/5 scale-[0.99]'
                : selectedFile
                ? 'border-[var(--green)]/60 bg-[var(--green)]/5'
                : 'border-[var(--border)] hover:border-[var(--blue)]/60 hover:bg-[var(--surface-hover)]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              onChange={handleFileInputChange}
              className="hidden"
            />

            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-transform ${
                isDragging
                  ? 'bg-[var(--blue)]/20 text-[var(--blue)] scale-110'
                  : selectedFile
                  ? 'bg-[var(--green)]/20 text-[var(--green)]'
                  : 'bg-[var(--surface)] text-[var(--muted)] border border-[var(--border)]'
              }`}
            >
              {selectedFile ? <FileSpreadsheet size={22} /> : <UploadCloud size={24} />}
            </div>

            {selectedFile ? (
              <div className="space-y-1">
                <div className="text-sm font-medium text-[var(--text)] flex items-center justify-center gap-2">
                  <span>{selectedFile.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--surface)] border border-[var(--border)] text-[var(--muted)]">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <p className="text-xs text-[var(--muted)]">
                  Click or drag another file to replace
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-medium text-[var(--text)]">
                  Drag & drop your holdings file here, or{' '}
                  <span className="text-[var(--blue)] underline">browse</span>
                </p>
                <p className="text-xs text-[var(--muted)]">
                  Supports Zerodha <code>holdings.csv</code>, Groww, Excel (.xlsx, .xls) up to 5 MB
                </p>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {uploadError && (
            <div className="p-3 rounded-lg bg-[var(--red)]/10 border border-[var(--red)]/30 text-[var(--red)] text-xs flex items-start gap-2 animate-fadeIn">
              <AlertCircle size={15} className="shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold">Upload Error: </span>
                <span>{uploadError}</span>
              </div>
              <button
                type="button"
                onClick={() => setUploadError(null)}
                className="hover:opacity-75"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-1">
            {selectedFile && (
              <button
                type="button"
                disabled={isUploading}
                onClick={handleReset}
                className="px-3 py-1.5 text-xs font-medium text-[var(--muted)] hover:text-[var(--text)] rounded-lg transition-colors border border-[var(--border)]"
              >
                Clear
              </button>
            )}

            <button
              type="button"
              disabled={!selectedFile || isUploading}
              onClick={handleUpload}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all shadow-sm ${
                !selectedFile || isUploading
                  ? 'bg-[var(--blue)]/50 cursor-not-allowed opacity-60'
                  : 'bg-[var(--blue)] hover:opacity-90 cursor-pointer active:scale-95'
              }`}
            >
              {isUploading ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  <span>Parsing & Enriching…</span>
                </>
              ) : (
                <>
                  <UploadCloud size={14} />
                  <span>Upload & Sync Portfolio</span>
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        /* Success Report View */
        <div className="space-y-4 animate-fadeIn">
          <div className="p-4 rounded-xl bg-[var(--green)]/10 border border-[var(--green)]/30 text-[var(--text)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-[var(--green)] font-semibold text-sm">
                <CheckCircle2 size={18} />
                <span>Holdings Imported Successfully!</span>
              </div>
              <span className="text-xs text-[var(--muted)] font-mono">{result.filename}</span>
            </div>
            <p className="text-xs text-[var(--muted)] mt-1">
              Successfully imported and enriched{' '}
              <strong className="text-[var(--text)]">{result.holdings_count}</strong> positions.
              Fundamental metrics and real-time analytics have been refreshed.
            </p>
          </div>

          {/* Summary KPI Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-[var(--bg)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Total Positions</div>
              <div className="text-base font-bold text-[var(--text)] mt-0.5">{result.holdings_count}</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--bg)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Total Investment</div>
              <div className="text-base font-bold text-[var(--text)] mt-0.5">{fmtCurrency(result.summary.total_investment)}</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--bg)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Current Value</div>
              <div className="text-base font-bold text-[var(--text)] mt-0.5">{fmtCurrency(result.summary.current_value)}</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--bg)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Unrealized P&L</div>
              <div
                className={`text-base font-bold mt-0.5 ${
                  result.summary.total_pnl >= 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'
                }`}
              >
                {fmtCurrency(result.summary.total_pnl)} ({result.summary.total_pnl_percentage.toFixed(2)}%)
              </div>
            </div>
          </div>

          {/* Skipped Rows Accordion (if any) */}
          {result.skipped_count > 0 && (
            <div className="border border-[var(--yellow)]/40 rounded-xl overflow-hidden bg-[var(--yellow)]/5">
              <button
                type="button"
                onClick={() => setShowSkipped((prev) => !prev)}
                className="w-full flex items-center justify-between p-3 text-xs font-medium text-[var(--text)] hover:bg-[var(--yellow)]/10 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2 text-[var(--yellow)]">
                  <AlertCircle size={15} />
                  <span>
                    {result.skipped_count} row{result.skipped_count > 1 ? 's were' : ' was'} skipped due to validation errors
                  </span>
                </div>
                {showSkipped ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>

              {showSkipped && (
                <div className="p-3 border-t border-[var(--yellow)]/20 overflow-x-auto text-xs">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="text-[var(--muted)] border-b border-[var(--border)]">
                        <th className="py-1 px-2 font-medium">Row #</th>
                        <th className="py-1 px-2 font-medium">Reason</th>
                        <th className="py-1 px-2 font-medium">Data Snippet</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.skipped_rows.map((sk) => (
                        <tr key={sk.row} className="border-b border-[var(--border)]/50">
                          <td className="py-1.5 px-2 font-mono text-[var(--muted)]">{sk.row}</td>
                          <td className="py-1.5 px-2 text-[var(--red)] font-medium">{sk.reason}</td>
                          <td className="py-1.5 px-2 font-mono text-[11px] text-[var(--muted)] truncate max-w-xs">
                            {JSON.stringify(sk.data)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Post-Upload Actions */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleReset}
              className="flex items-center gap-1.5 text-xs text-[var(--blue)] hover:underline font-medium cursor-pointer"
            >
              <FileText size={14} />
              <span>Upload another file</span>
            </button>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-1.5 bg-[var(--surface-hover)] border border-[var(--border)] text-xs font-semibold rounded-lg text-[var(--text)] hover:bg-[var(--surface)] transition-colors cursor-pointer"
              >
                Done
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
