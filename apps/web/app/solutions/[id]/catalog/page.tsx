'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  ColumnDef
} from '@tanstack/react-table';
import { Loader2, Search, Filter, Database, FileText, Activity, Table, Code, Box, Layers } from 'lucide-react';
import Link from 'next/link';

// Color Mapping (Matches Graph View)
const NODE_COLORS: Record<string, { bg: string, border: string, text: string }> = {
  'PIPELINE': { bg: '#f3e8ff', border: '#9333ea', text: '#6b21a8' }, // Purple
  'PROCESS': { bg: '#f3e8ff', border: '#9333ea', text: '#6b21a8' },
  'SCRIPT': { bg: '#e0f2fe', border: '#0284c7', text: '#0369a1' }, // Blue
  'FILE': { bg: '#e0f2fe', border: '#0284c7', text: '#0369a1' },
  'TABLE': { bg: '#dcfce7', border: '#16a34a', text: '#15803d' }, // Green
  'VIEW': { bg: '#dcfce7', border: '#16a34a', text: '#15803d' },
  'DATABASE': { bg: '#ffedd5', border: '#ea580c', text: '#c2410c' }, // Orange
  'PACKAGE': { bg: '#fee2e2', border: '#ef4444', text: '#b91c1c' }, // Red
  'DEFAULT': { bg: '#f3f4f6', border: '#9ca3af', text: '#374151' } // Gray
};

interface CatalogPageProps {
  params: {
    id: string;
  };
}

export default function CatalogPage({ params }: CatalogPageProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('ALL');
  const [search, setSearch] = useState('');
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 50,
  });
  const [totalCount, setTotalCount] = useState(0);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [details, setDetails] = useState<any>(null);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${params.id}/assets`, {
        params: {
          type: filterType,
          search: search,
          limit: pagination.pageSize,
          offset: pagination.pageIndex * pagination.pageSize
        }
      });
      setData(res.data.data || []);
      setTotalCount(res.data.count || 0);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [filterType, search, pagination.pageIndex, pagination.pageSize]);

  const columns: ColumnDef<any>[] = [
    {
      accessorKey: 'asset_type',
      header: 'Type',
      cell: info => {
        const val = (info.getValue() as string).toUpperCase();
        const colors = NODE_COLORS[val] || NODE_COLORS['DEFAULT'];

        let Icon = FileText;
        if (val === 'TABLE' || val === 'VIEW') Icon = Table;
        if (val === 'PIPELINE' || val === 'PROCESS') Icon = Activity;
        if (val === 'DATABASE') Icon = Database;
        if (val === 'SCRIPT') Icon = Code;
        if (val === 'PACKAGE') Icon = Box;

        return (
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border"
            style={{
              backgroundColor: colors.bg,
              borderColor: colors.border,
              color: colors.text
            }}
          >
            <Icon size={12} />
            {val}
          </span>
        );
      }
    },
    {
      accessorKey: 'name_display',
      header: 'Name',
      cell: info => <span className="font-semibold text-gray-900 dark:text-gray-100">{info.getValue() as string}</span>
    },
    {
      accessorKey: 'system',
      header: 'System',
      cell: info => (
        <span className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded dark:bg-zinc-800">
          {info.getValue() as string || 'N/A'}
        </span>
      )
    },
    {
      accessorKey: 'created_at',
      header: 'Discovered',
      cell: info => <span className="text-gray-500 text-xs">{new Date(info.getValue() as string).toLocaleDateString()}</span>
    }
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: Math.ceil(totalCount / pagination.pageSize),
    state: {
      pagination,
    },
    onPaginationChange: setPagination,
  });

  const handleRowClick = async (asset: any) => {
    setSelectedAsset(asset);
    setDetailsLoading(true);
    setDetails(null);
    try {
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/assets/${asset.asset_id}/details`);
      setDetails(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailsLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Main Content: Table */}
      <div className={`flex-1 p-6 overflow-hidden flex flex-col ${selectedAsset ? 'w-2/3' : 'w-full'}`}>
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <Link href={`/solutions/${params.id}`} className="text-gray-500 hover:text-gray-900">&larr; Back to Graph</Link>
            <h1 className="text-2xl font-bold">Asset Catalog</h1>
          </div>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search assets..."
                className="pl-9 h-9 w-[200px] lg:w-[300px] rounded-md border border-gray-200 bg-white px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select
              className="h-9 rounded-md border border-gray-200 bg-white px-3 py-1 text-sm shadow-sm focus-visible:outline-none"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="ALL">All Types</option>
              <option value="TABLE">Tables</option>
              <option value="FILE">Files</option>
              <option value="PIPELINE">Pipelines</option>
            </select>
          </div>
        </div>

        <div className="border rounded-md flex-1 overflow-auto bg-white dark:bg-zinc-900">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-zinc-800 sticky top-0">
              {table.getHeaderGroups().map(headerGroup => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map(header => (
                    <th key={header.id} className="px-6 py-3 font-medium">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={columns.length} className="text-center py-10">
                    <Loader2 className="animate-spin inline mr-2" /> Loading...
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="text-center py-10 text-gray-500">
                    No assets found.
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map(row => {
                  const assetType = (row.original.asset_type || 'DEFAULT').toUpperCase();
                  const colors = NODE_COLORS[assetType] || NODE_COLORS['DEFAULT'];

                  return (
                    <tr
                      key={row.id}
                      onClick={() => handleRowClick(row.original)}
                      className={`border-b hover:bg-gray-50 dark:hover:bg-zinc-800 cursor-pointer transition-colors ${selectedAsset?.asset_id === row.original.asset_id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}
                      style={{ borderLeft: `4px solid ${colors.border}` }}
                    >
                      {row.getVisibleCells().map(cell => (
                        <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-end gap-2 py-4">
          <span className="text-sm text-gray-500">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <button
            className="border rounded px-2 py-1 text-sm disabled:opacity-50"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </button>
          <button
            className="border rounded px-2 py-1 text-sm disabled:opacity-50"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </button>
        </div>
      </div>

      {/* Side Panel: Details */}
      {selectedAsset && (
        <div className="w-1/3 border-l bg-white dark:bg-zinc-900 overflow-y-auto p-6 shadow-xl z-10 transition-all duration-300">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-xl font-bold break-words w-full">{selectedAsset.name_display}</h2>
            <button onClick={() => setSelectedAsset(null)} className="text-gray-400 hover:text-gray-600">
              &times;
            </button>
          </div>

          {detailsLoading ? (
            <div className="flex justify-center py-10"><Loader2 className="animate-spin" /></div>
          ) : details ? (
            <div className="space-y-6">
              {/* Business Intent (New) */}
              {selectedAsset.tags?.business_intent && (
                <div>
                  <h3 className="text-sm font-semibold text-primary uppercase tracking-wider mb-2 flex items-center gap-2">
                    <Activity size={14} /> Business Intent
                  </h3>
                  <div className="bg-primary/5 p-4 rounded-lg text-sm text-foreground border border-primary/10 italic">
                    "{selectedAsset.tags.business_intent}"
                  </div>
                </div>
              )}

              {/* Transformation Logic (New for Tasks) */}
              {selectedAsset.tags?.transformation_logic && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                    <Code size={14} /> Transformation Logic
                  </h3>
                  <div className="bg-slate-950 p-4 rounded-lg overflow-x-auto border border-white/10 shadow-inner">
                    <pre className="text-xs text-blue-300 font-mono leading-relaxed whitespace-pre-wrap">
                      {selectedAsset.tags.transformation_logic}
                    </pre>
                  </div>
                </div>
              )}

              {/* Attributes & Columns */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                  <Database size={14} /> Metadata & Schema
                </h3>
                <div className="bg-gray-50 dark:bg-zinc-800 p-3 rounded text-sm space-y-3">
                  <div className="flex justify-between border-b border-border/50 pb-1">
                    <span className="text-gray-500">Type:</span>
                    <span className="font-medium">{selectedAsset.asset_type}</span>
                  </div>
                  <div className="flex justify-between border-b border-border/50 pb-1">
                    <span className="text-gray-500">System:</span>
                    <span className="font-medium">{selectedAsset.system || 'Unknown'}</span>
                  </div>

                  {/* Enhanced Columns Display */}
                  {selectedAsset.tags?.columns && Array.isArray(selectedAsset.tags.columns) && (
                    <div className="pt-2">
                      <span className="text-gray-500 text-xs font-bold block mb-2">COLUMNS:</span>
                      <ul className="space-y-2 list-none text-xs">
                        {selectedAsset.tags.columns.map((col: any, i: number) => {
                          const isObj = typeof col === 'object' && col !== null;
                          return (
                            <li key={i} className="pb-2 border-b border-border/30 last:border-0">
                              <div className="font-bold text-foreground">
                                {isObj ? col.name : col}
                                {isObj && col.type && <span className="ml-1 text-[10px] text-muted-foreground uppercase">({col.type})</span>}
                              </div>
                              {isObj && col.logic && (
                                <div className="text-muted-foreground mt-0.5 italic">{col.logic}</div>
                              )}
                              {isObj && col.source && (
                                <div className="text-[10px] text-primary/70 font-mono mt-0.5">Src: {col.source}</div>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  )}

                  {/* Other Tags */}
                  {selectedAsset.tags && Object.entries(selectedAsset.tags)
                    .filter(([k]) => !['columns', 'transformation_logic', 'business_intent', 'business_rule'].includes(k))
                    .map(([k, v]) => (
                      <div key={k} className="flex justify-between pt-1">
                        <span className="text-gray-500 capitalize">{k}:</span>
                        <span className="font-medium truncate max-w-[200px]" title={String(v)}>{String(v)}</span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Relationships */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Relationships</h3>

                {details.outgoing_edges?.length > 0 && (
                  <div className="mb-4">
                    <span className="text-xs font-medium text-blue-600 mb-1 block">Outgoing (Depends On / Writes To)</span>
                    <ul className="space-y-2">
                      {details.outgoing_edges.map((edge: any) => (
                        <li key={edge.edge_id} className="text-sm border p-2 rounded hover:bg-gray-50 flex justify-between items-center group">
                          <div>
                            <span className="text-gray-500 text-xs mr-2">--[{edge.edge_type}]--&gt;</span>
                            <span className="font-medium">{edge.to_asset.name_display}</span>
                          </div>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${edge.confidence > 0.7 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                            {Math.round(edge.confidence * 100)}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {details.incoming_edges?.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-purple-600 mb-1 block">Incoming (Used By)</span>
                    <ul className="space-y-2">
                      {details.incoming_edges.map((edge: any) => (
                        <li key={edge.edge_id} className="text-sm border p-2 rounded hover:bg-gray-50 flex justify-between items-center">
                          <div>
                            <span className="font-medium">{edge.from_asset.name_display}</span>
                            <span className="text-gray-500 text-xs ml-2">--[{edge.edge_type}]--&gt;</span>
                          </div>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${edge.confidence > 0.7 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                            {Math.round(edge.confidence * 100)}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {(!details.outgoing_edges?.length && !details.incoming_edges?.length) && (
                  <p className="text-sm text-gray-400 italic">No relationships found.</p>
                )}
              </div>

              {/* Evidence */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Evidence & Lineage</h3>
                {details.evidences?.length > 0 ? (
                  <div className="space-y-3">
                    {details.evidences.map((item: any) => (
                      <div key={item.evidence.evidence_id} className="border rounded p-3 bg-slate-50 dark:bg-zinc-800/50">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-xs font-mono bg-white border px-1 rounded">{item.evidence.kind}</span>
                          <span className="text-xs text-gray-400">{item.evidence.file_path.split('/').pop()}</span>
                        </div>
                        {item.evidence.snippet && (
                          <pre className="text-xs overflow-x-auto bg-gray-100 dark:bg-black p-2 rounded text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                            {item.evidence.snippet}
                          </pre>
                        )}
                        {item.evidence.locator && (
                          <div className="mt-1 text-[10px] text-gray-400">
                            Lines: {item.evidence.locator.line_start}-{item.evidence.locator.line_end}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 italic">No direct evidence snippets linked.</p>
                )}
              </div>

            </div>
          ) : (
            <p className="text-red-500">Failed to load details.</p>
          )}
        </div>
      )}
    </div>
  );
}