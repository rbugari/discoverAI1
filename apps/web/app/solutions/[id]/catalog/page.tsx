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
import { Loader2, Search, Filter, Database, FileText, Activity, Table, Code, Box, Layers, LayoutGrid, X } from 'lucide-react';
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
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);

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

  const fetchAvailableTypes = async () => {
    try {
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/solutions/${params.id}/asset-types`);
      setAvailableTypes(res.data.types || []);
    } catch (e) {
      console.error("Error fetching asset types:", e);
    }
  };

  useEffect(() => {
    fetchAvailableTypes();
  }, [params.id]);

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
    <div className="flex h-[calc(100vh-64px)] p-6 gap-6 bg-slate-950/20">
      {/* Main Content: Table */}
      <div className={`flex-1 overflow-hidden flex flex-col ${selectedAsset ? 'w-2/3' : 'w-full'} transition-all duration-500 ease-out`}>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div className="flex flex-col gap-1">
            <Link
              href={`/solutions/${params.id}`}
              className="text-[10px] font-black uppercase tracking-widest text-muted-foreground hover:text-primary flex items-center gap-1 transition-colors mb-2"
            >
              &larr; Return to Graph
            </Link>
            <h1 className="text-3xl font-black tracking-tighter text-foreground flex items-center gap-3">
              <LayoutGrid className="text-primary" size={28} /> Asset Catalog
            </h1>
            <p className="text-muted-foreground font-medium text-sm max-w-xl">
              Comprehensive inventory of all discovered technical assets and their metadata.
            </p>
          </div>
          <div className="flex gap-3 items-center">
            <div className="relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <input
                type="text"
                placeholder="Search assets..."
                className="pl-10 h-10 w-[200px] lg:w-[300px] rounded-xl border border-border bg-muted/40 backdrop-blur-sm px-4 py-2 text-sm shadow-inner transition-all focus:outline-none focus:ring-2 focus:ring-primary/40 focus:bg-muted/60"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <select
                className="h-10 pl-10 pr-8 rounded-xl border border-border bg-muted/40 backdrop-blur-sm text-sm shadow-inner transition-all focus:outline-none focus:ring-2 focus:ring-primary/40 focus:bg-muted/60 appearance-none cursor-pointer font-medium"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="ALL">All Types</option>
                {availableTypes.map(type => (
                  <option key={type} value={type}>
                    {type.charAt(0) + type.slice(1).toLowerCase().replace(/_/g, ' ')}s
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="border border-border/50 rounded-[2rem] flex-1 overflow-hidden bg-card/50 backdrop-blur-md shadow-2xl flex flex-col relative">
          <div className="overflow-auto flex-1 custom-scrollbar">
            <table className="w-full text-sm text-left border-collapse">
              <thead className="text-[10px] text-muted-foreground uppercase font-black bg-muted/80 backdrop-blur-md sticky top-0 z-20 border-b border-border/50 tracking-widest">
                {table.getHeaderGroups().map(headerGroup => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map(header => (
                      <th key={header.id} className="px-6 py-4 font-bold">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody className="divide-y divide-border/30">
                {loading ? (
                  <tr>
                    <td colSpan={columns.length} className="text-center py-20">
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="animate-spin text-primary" size={32} />
                        <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Fetching Assets...</span>
                      </div>
                    </td>
                  </tr>
                ) : data.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length} className="text-center py-20 text-gray-500 group">
                      <div className="flex flex-col items-center justify-center gap-4 opacity-50">
                        <div className="p-6 bg-muted/50 rounded-full text-muted-foreground/30 ring-8 ring-muted/20">
                          <Search size={48} strokeWidth={1} />
                        </div>
                        <p className="text-muted-foreground font-black uppercase tracking-widest text-xs">No assets found</p>
                        <button
                          onClick={() => { setSearch(''); setFilterType('ALL'); }}
                          className="text-[10px] font-bold text-primary hover:underline uppercase tracking-wide"
                        >
                          Reset Filters
                        </button>
                      </div>
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
                        className={`hover:bg-primary/5 cursor-pointer transition-colors group ${selectedAsset?.asset_id === row.original.asset_id ? 'bg-primary/5' : ''}`}
                      >
                        {row.getVisibleCells().map(cell => (
                          <td key={cell.id} className="px-6 py-4 whitespace-nowrap first:border-l-4" style={cell.column.id === 'asset_type' ? { borderLeftColor: colors.border } : {}}>
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

          {/* Footer Pagination */}
          <div className="p-4 border-t border-border/50 bg-muted/30 flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest">
              Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
            </span>
            <div className="flex gap-2">
              <button
                className="px-3 py-1.5 rounded-lg border border-border/50 bg-background hover:bg-muted text-[10px] font-bold uppercase tracking-wider disabled:opacity-50 transition-colors"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                Previous
              </button>
              <button
                className="px-3 py-1.5 rounded-lg border border-border/50 bg-background hover:bg-muted text-[10px] font-bold uppercase tracking-wider disabled:opacity-50 transition-colors"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Side Panel: Details */}
      {selectedAsset && (
        <div className="w-1/3 border border-border/50 bg-card/80 backdrop-blur-xl rounded-[2.5rem] overflow-hidden shadow-2xl flex flex-col animate-in slide-in-from-right-10 duration-500">
          <div className="p-8 border-b border-border/50 bg-gradient-to-b from-muted/50 to-transparent">
            <div className="flex justify-between items-start mb-4">
              <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground border border-border px-2 py-0.5 rounded-md bg-background/50">Details Inspector</span>
              <button onClick={() => setSelectedAsset(null)} className="text-muted-foreground hover:text-foreground transition-colors p-1 hover:bg-background/50 rounded-full">
                <X size={16} />
              </button>
            </div>
            <h2 className="text-2xl font-black tracking-tight break-words w-full leading-tight">
              {selectedAsset.name_display === 'Unknown' || !selectedAsset.name_display
                ? (selectedAsset.asset_type + ': ' + selectedAsset.asset_id.slice(0, 8))
                : selectedAsset.name_display}
            </h2>
            <div className="flex items-center gap-2 mt-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-muted-foreground">Active Asset</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
            {detailsLoading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-2 opacity-50">
                <Loader2 className="animate-spin text-primary" size={24} />
                <span className="text-[10px] font-black uppercase tracking-widest">Loading Metadata...</span>
              </div>
            ) : details ? (
              <div className="space-y-8">
                {/* Business Intent (New) */}
                {selectedAsset.tags?.business_intent && (
                  <div>
                    <h3 className="text-[10px] font-black text-primary uppercase tracking-widest mb-3 flex items-center gap-2">
                      <Activity size={12} /> Business Intent
                    </h3>
                    <div className="bg-primary/5 p-5 rounded-2xl text-sm font-medium text-foreground border border-primary/10 italic leading-relaxed">
                      "{selectedAsset.tags.business_intent}"
                    </div>
                  </div>
                )}

                {/* Transformation Logic (New for Tasks) */}
                {selectedAsset.tags?.transformation_logic && (
                  <div>
                    <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-3 flex items-center gap-2">
                      <Code size={12} /> Transformation Logic
                    </h3>
                    <div className="bg-[#0d1117] p-5 rounded-2xl overflow-x-auto border border-white/5 shadow-inner group relative">
                      <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-white/10 text-[8px] text-white/40 font-mono uppercase">SQL</div>
                      <pre className="text-[10px] text-blue-300 font-mono leading-relaxed whitespace-pre-wrap">
                        {selectedAsset.tags.transformation_logic}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Attributes & Columns */}
                <div>
                  <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-3 flex items-center gap-2">
                    <Database size={12} /> Metadata & Schema
                  </h3>
                  <div className="bg-background/50 border border-border/50 p-5 rounded-[1.5rem] text-sm space-y-3 shadow-sm">
                    <div className="flex justify-between border-b border-border/30 pb-2">
                      <span className="text-muted-foreground text-xs font-bold">Type</span>
                      <span className="font-bold text-foreground text-xs">{selectedAsset.asset_type}</span>
                    </div>
                    <div className="flex justify-between border-b border-border/30 pb-2">
                      <span className="text-muted-foreground text-xs font-bold">System</span>
                      <span className="font-bold font-mono text-xs bg-muted/50 px-1.5 py-0.5 rounded text-foreground">{selectedAsset.system || 'Unknown'}</span>
                    </div>

                    {/* Enhanced Columns Display */}
                    {selectedAsset.tags?.columns && Array.isArray(selectedAsset.tags.columns) && (
                      <div className="pt-2">
                        <span className="text-[9px] font-black text-muted-foreground uppercase tracking-widest block mb-3">Schema Definition</span>
                        <ul className="space-y-2 list-none text-xs">
                          {selectedAsset.tags.columns.map((col: any, i: number) => {
                            const isObj = typeof col === 'object' && col !== null;
                            return (
                              <li key={i} className="pb-2 border-b border-border/30 last:border-0">
                                <div className="font-bold text-foreground flex items-center justify-between">
                                  {isObj ? col.name : col}
                                  {isObj && col.type && <span className="text-[9px] text-muted-foreground font-mono bg-muted/50 px-1.5 rounded">{col.type}</span>}
                                </div>
                                {isObj && col.logic && (
                                  <div className="text-muted-foreground mt-1 text-[10px] pl-2 border-l-2 border-primary/20">{col.logic}</div>
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}

                    {/* Clean attribute loop */}
                    {selectedAsset.tags && Object.entries(selectedAsset.tags)
                      .filter(([k]) => !['columns', 'transformation_logic', 'business_intent', 'business_rule'].includes(k))
                      .map(([k, v]) => (
                        <div key={k} className="flex justify-between pt-1">
                          <span className="text-muted-foreground capitalize text-xs">{k}</span>
                          <span className="font-medium text-xs truncate max-w-[150px]" title={String(v)}>{String(v)}</span>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Relationships */}
                <div>
                  <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-3">Lineage Connections</h3>

                  {details.outgoing_edges?.length > 0 && (
                    <div className="mb-4">
                      <span className="text-[9px] font-bold text-blue-500 mb-2 block uppercase tracking-wide">Outgoing (Downstream)</span>
                      <ul className="space-y-2">
                        {details.outgoing_edges.map((edge: any) => (
                          <li key={edge.edge_id} className="text-sm border border-border/50 p-3 rounded-xl bg-background/40 hover:bg-background hover:border-blue-500/30 transition-all flex justify-between items-center group">
                            <div className="flex items-center gap-2 overflow-hidden">
                              <span className="text-[9px] font-mono text-muted-foreground whitespace-nowrap">--[{edge.edge_type}]--&gt;</span>
                              <span className="font-bold text-xs truncate">{edge.to_asset.name_display}</span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {details.incoming_edges?.length > 0 && (
                    <div>
                      <span className="text-[9px] font-bold text-purple-500 mb-2 block uppercase tracking-wide">Incoming (Upstream)</span>
                      <ul className="space-y-2">
                        {details.incoming_edges.map((edge: any) => (
                          <li key={edge.edge_id} className="text-sm border border-border/50 p-3 rounded-xl bg-background/40 hover:bg-background hover:border-purple-500/30 transition-all flex justify-between items-center group">
                            <div className="flex items-center gap-2 overflow-hidden">
                              <span className="font-bold text-xs truncate">{edge.from_asset.name_display}</span>
                              <span className="text-[9px] font-mono text-muted-foreground whitespace-nowrap">&lt;--[{edge.edge_type}]--</span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

              </div>
            ) : (
              <p className="text-red-500 font-bold text-center text-xs uppercase tracking-widest">Failed to retrieve asset details.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}