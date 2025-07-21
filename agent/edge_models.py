"""
Edge models for the knowledge graph.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Employment(BaseModel):
    """Employment relationship between a person and company."""
    position: Optional[str] = Field(None, description="Job title or position")
    start_date: Optional[str] = Field(None, description="Employment start date (flexible format)")
    end_date: Optional[str] = Field(None, description="Employment end date (flexible format)")
    salary: Optional[float] = Field(None, description="Annual salary in USD")
    is_current: Optional[bool] = Field(None, description="Whether employment is current")
    department: Optional[str] = Field(None, description="Department or division")
    employment_type: Optional[str] = Field(None, description="Type of employment (full-time, part-time, contract)")


class Leadership(BaseModel):
    """Leadership or executive relationship between a person and company."""
    role: Optional[str] = Field(None, description="Leadership role (CEO, CTO, Chairman, etc.)")
    start_date: Optional[str] = Field(None, description="Leadership start date (flexible format)")
    end_date: Optional[str] = Field(None, description="Leadership end date (flexible format)")
    is_current: Optional[bool] = Field(None, description="Whether leadership role is current")
    board_member: Optional[bool] = Field(None, description="Whether person is a board member")


class Investment(BaseModel):
    """Investment relationship between entities."""
    amount: Optional[float] = Field(None, description="Investment amount in USD")
    investment_type: Optional[str] = Field(None, description="Type of investment (equity, debt, etc.)")
    stake_percentage: Optional[float] = Field(None, description="Percentage ownership")
    investment_date: Optional[str] = Field(None, description="Date of investment (flexible format)")
    round_type: Optional[str] = Field(None, description="Investment round type (Series A, B, etc.)")


class Partnership(BaseModel):
    """Partnership relationship between companies."""
    partnership_type: Optional[str] = Field(None, description="Type of partnership")
    duration: Optional[str] = Field(None, description="Expected duration")
    deal_value: Optional[float] = Field(None, description="Financial value of partnership")
    start_date: Optional[str] = Field(None, description="Partnership start date (flexible format)")
    end_date: Optional[str] = Field(None, description="Partnership end date (flexible format)")


class Ownership(BaseModel):
    """Ownership relationship between entities."""
    ownership_percentage: Optional[float] = Field(None, description="Percentage of ownership")
    ownership_type: Optional[str] = Field(None, description="Type of ownership (majority, minority, etc.)")
    acquisition_date: Optional[str] = Field(None, description="Date of acquisition (flexible format)")
    acquisition_price: Optional[float] = Field(None, description="Acquisition price in USD")
