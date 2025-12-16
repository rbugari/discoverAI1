import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const solutionId = params.id;
    
    // Backend URL (Server to Server)
    // We use 127.0.0.1 directly to ensure no localhost resolution issues on server side
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    
    console.log(`Proxying chat request for ${solutionId} to ${backendUrl}`);
    
    const response = await axios.post(`${backendUrl}/solutions/${solutionId}/chat`, body);
    
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error("Proxy Chat Error:", error.message);
    if (error.response) {
        console.error("Backend Response:", error.response.data);
        return NextResponse.json(error.response.data, { status: error.response.status });
    }
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: 500 }
    );
  }
}