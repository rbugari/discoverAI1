import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const solutionId = params.id;
    
    // Backend URL (Server to Server)
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    
    console.log(`Proxying DELETE request for ${solutionId} to ${backendUrl}`);
    
    const response = await axios.delete(`${backendUrl}/solutions/${solutionId}`);
    
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error("Proxy DELETE Error:", error.message);
    if (error.response) {
        return NextResponse.json(error.response.data, { status: error.response.status });
    }
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: 500 }
    );
  }
}